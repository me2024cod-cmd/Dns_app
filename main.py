import socket
import time
import statistics
import threading
import tkinter as tk

class CloudflareDNSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Matrix Pro - Cloudflare Style")
        self.root.geometry("400x700")
        self.root.configure(bg="#1e1e1e")

        # رنگ‌بندی تم تاریک و حرفه‌ای (سبک کلودفلر)
        self.BG_COLOR = "#1e1e1e"
        self.PANEL_COLOR = "#2d2d2d"
        self.TEXT_COLOR = "#ffffff"
        self.ACCENT_COLOR = "#f38020" # نارنجی کلودفلر

        # عنوان برنامه
        title_lbl = tk.Label(root, text="DNS Latency & Jitter Tool", font=("Arial", 16, "bold"), bg=self.BG_COLOR, fg=self.ACCENT_COLOR)
        title_lbl.pack(pady=10)

        # فیلد دامنه هدف
        dom_frame = tk.Frame(root, bg=self.BG_COLOR)
        dom_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(dom_frame, text="دامنه تست (Target Domain):", bg=self.BG_COLOR, fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_domain = tk.Entry(dom_frame, bg=self.PANEL_COLOR, fg=self.TEXT_COLOR, insertbackground="white", font=("Arial", 11), relief="flat")
        self.entry_domain.pack(fill="x", ippad=5, pady=2)
        self.entry_domain.insert(0, "google.com")

        # فیلد ورود دستی IPها
        ip_frame = tk.Frame(root, bg=self.BG_COLOR)
        ip_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(ip_frame, text="آی‌پی‌های DNS (با کاما یا فاصله جدا کنید):", bg=self.BG_COLOR, fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_ips = tk.Entry(ip_frame, bg=self.PANEL_COLOR, fg=self.TEXT_COLOR, insertbackground="white", font=("Arial", 11), relief="flat")
        self.entry_ips.pack(fill="x", ippad=5, pady=2)
        self.entry_ips.insert(0, "1.1.1.1, 8.8.8.8, 9.9.9.9, 78.157.42.100, 178.22.122.100, 4.2.2.4")

        # دکمه اجرای تست
        self.btn_run = tk.Button(root, text="شروع تست هوشمند (UDP & TCP)", bg=self.ACCENT_COLOR, fg="white", font=("Arial", 11, "bold"), relief="flat", command=self.start_thread)
        self.btn_run.pack(fill="x", padx=15, pady=15, ipadi=5)

        # کادر نمایش نتایج (جدول خروجی)
        self.text_results = tk.Text(root, bg=self.PANEL_COLOR, fg="#00ffcc", font=("Courier", 9), relief="flat")
        self.text_results.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.text_results.insert("1.0", "آماده برای تست...\n- پورت ۵۳ (UDP و TCP)\n- فیلتر خودکار بالای 3000ms\n- نمایش ۵۰ تای برتر\n")

    def build_dns_query(self, domain):
        parts = domain.split(".")
        qname = b""
        for part in parts:
            qname += bytes([len(part)]) + part.encode("utf-8")
        qname += b"\x00"
        header = b"\xaa\xaa\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        tail = b"\x00\x01\x00\x01"
        return header + qname + tail

    def test_udp(self, ip, query_bytes):
        latencies = []
        for _ in range(3):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.2)
            start = time.time()
            try:
                sock.sendto(query_bytes, (ip, 53))
                sock.recvfrom(512)
                latencies.append((time.time() - start) * 1000)
            except:
                pass
            finally:
                sock.close()
        if not latencies:
            return None, None
        return round(sum(latencies)/len(latencies), 2), round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0

    def test_tcp(self, ip, query_bytes):
        latencies = []
        for _ in range(3):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.2)
            start = time.time()
            try:
                sock.connect((ip, 53))
                packet = b"\x00" + len(query_bytes).to_bytes(1, "big") + query_bytes
                sock.sendall(packet)
                sock.recv(512)
                latencies.append((time.time() - start) * 1000)
            except:
                pass
            finally:
                sock.close()
        if not latencies:
            return None, None
        return round(sum(latencies)/len(latencies), 2), round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0

    def start_thread(self):
        threading.Thread(target=self.run_benchmark, daemon=True).start()

    def run_benchmark(self):
        self.btn_run.config(state="disabled", text="در حال تست و بررسی...")
        domain = self.entry_domain.get().strip() or "google.com"
        raw_ips = self.entry_ips.get().strip()
        
        ips = [i.strip() for i in raw_ips.replace(",", " ").split() if i.strip()]
        query = self.build_dns_query(domain)
        results = []

        self.text_results.delete("1.0", "end")
        self.text_results.insert("end", f"در حال تست {len(ips)} سرور روی دامنه '{domain}'...\n\n")

        for ip in ips:
            u_p, u_j = self.test_udp(ip, query)
            t_p, t_j = self.test_tcp(ip, query)

            valid_u = u_p is not None and u_p < 3000
            valid_t = t_p is not None and t_p < 3000

            if valid_u or valid_t:
                results.append({
                    "ip": ip,
                    "udp_p": u_p if valid_u else 9999,
                    "udp_j": u_j if valid_u else 0,
                    "tcp_p": t_p if valid_t else 9999,
                    "tcp_j": t_j if valid_t else 0
                })

        results = sorted(results, key=lambda x: x["udp_p"])[:50]

        output = f"{'IP Address':<15} | {'U-Ping':<7} | {'T-Ping'}\n" + "-"*35 + "\n"
        if results:
            for r in results:
                up = f"{r['udp_p']}ms" if r['udp_p'] != 9999 else "Timeout"
                tp = f"{r['tcp_p']}ms" if r['tcp_p'] != 9999 else "Timeout"
                output += f"{r['ip']:<15} | {up:<7} | {tp}\n"
        else:
            output += "هیچ سروری زیر ۳۰۰۰ms پاسخ نداد یا فیلتر شد.\n"

        self.text_results.delete("1.0", "end")
        self.text_results.insert("end", output)
        self.btn_run.config(state="normal", text="شروع تست هوشمند (UDP & TCP)")

if __name__ == "__main__":
    root = tk.Tk()
    app = CloudflareDNSApp(root)
    root.mainloop()
