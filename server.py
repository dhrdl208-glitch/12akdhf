import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
import datetime
import os
import json
import requests
import pyautogui
import pyperclip

try:
    import pygetwindow as gw
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "PyGetWindow"])
    import pygetwindow as gw

LICENSE_FILE = "license.json"
is_running = False

# ================= 서버 주소 설정 (본인의 실제 렌더 주소로 수정해주세요!) =================
# 예시: "https://랜덤이름.onrender.com/api/verify"
SERVER_URL = "https://여기에_본인의_실제_렌더_주소_입력.onrender.com/api/verify"

# ================= 테마 컬러 설정 =================
BG_COLOR = "#f8fafc"
CARD_BG = "#ffffff"
PRIMARY_COLOR = "#4f46e5"
PRIMARY_HOVER = "#4338ca"
TEXT_MAIN = "#0f172a"
TEXT_SUB = "#64748b"
BORDER_COLOR = "#e2e8f0"

# ================= 라이선스 검증 함수 =================
def load_license():
    if not os.path.exists(LICENSE_FILE):
        return None
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_license(key, expiry_date):
    data = {"key": key, "expiry": expiry_date}
    try:
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"라이선스 파일 저장 경고: {e}")

def verify_key_logic(input_key):
    input_key = input_key.strip()
    if not input_key:
        return False, "키를 입력해주세요."
    
    try:
        # 서버로 데이터 전송 (헤더 명시)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(SERVER_URL, json={"key": input_key}, headers=headers, timeout=30)
        
        # 서버 응답 상태 코드 확인 (200이 아니면 에러 내용 파악)
        if response.status_code != 200:
            return False, f"서버 오류 발생 (코드: {response.status_code})\n서버 상태를 확인해주세요."
            
        data = response.json()
        
        if data.get("success") == True:
            expiry_str = data.get("expiry")
            save_license(input_key, expiry_str)
            return True, expiry_str
        else:
            return False, data.get("message", "유효하지 않거나 삭제된 인증 키입니다.")
    except Exception as e:
        return False, f"서버 연결 실패:\n{e}"

# ================= 인증 창 클래스 =================
class LicenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이상봇 - 라이선스 인증")
        self.root.geometry("420x260")
        self.root.config(bg=BG_COLOR)
        self.root.resizable(False, False)

        # 상단 타이틀 영역
        title_frame = tk.Frame(root, bg=BG_COLOR)
        title_frame.pack(pady=(25, 10))

        tk.Label(title_frame, text="⚡ 이상봇 베타버전", font=("Pretendard", 14, "bold"), fg=PRIMARY_COLOR, bg=BG_COLOR).pack(anchor="center")
        tk.Label(title_frame, text="구매하신 개인 인증 키를 입력해 주세요.", font=("Pretendard", 10), fg=TEXT_SUB, bg=BG_COLOR).pack(anchor="center", pady=(4, 0))

        # 입력 필드
        self.entry_key = tk.Entry(root, width=32, font=("Consolas", 12), justify="center", bd=1, relief="solid")
        self.entry_key.pack(pady=10)
        self.entry_key.config(highlightbackground=BORDER_COLOR)

        # 인증 버튼
        self.btn_verify = tk.Button(root, text="인증하기", bg=PRIMARY_COLOR, fg="white", font=("Pretendard", 11, "bold"), width=20, pady=6, bd=0, cursor="hand2", command=self.check_key)
        self.btn_verify.pack(pady=10)

        # 기존 인증 정보 확인
        lic = load_license()
        if lic:
            try:
                expiry_dt = datetime.datetime.strptime(lic["expiry"], "%Y-%m-%d %H:%M:%S")
                if expiry_dt > datetime.datetime.now():
                    self.root.destroy()
                    start_main_program()
                else:
                    messagebox.showwarning("만료됨", "사용 기간이 만료되었습니다. 새로운 키를 입력해주세요.")
            except:
                pass

    def check_key(self):
        key = self.entry_key.get()
        success, result_msg = verify_key_logic(key)
        if success:
            messagebox.showinfo("성공", f"인증이 완료되었습니다!\n만료일시: {result_msg}")
            self.root.destroy()
            start_main_program()
        else:
            messagebox.showerror("실패", result_msg)

# ================= 메인 프로그램 로직 =================
def log_message(text):
    text_log.config(state="normal")
    text_log.insert(tk.END, text + "\n")
    text_log.see(tk.END)
    text_log.config(state="disabled")

def activate_kakaotalk():
    try:
        windows = gw.getWindowsWithTitle('카카오톡')
        if not windows:
            windows = gw.getWindowsWithTitle('KakaoTalk')
        for win in windows:
            title = win.title.strip()
            if title in ['', '카카오톡', 'KakaoTalk']:
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(1)
                return True
        if windows:
            kakao = windows[0]
            if kakao.isMinimized:
                kakao.restore()
            kakao.activate()
            time.sleep(1)
            return True
        return False
    except:
        return False

def run_sending_loop(rooms, message, delay, interval_min, is_repeat):
    global is_running
    cycle_count = 1
    try:
        while is_running:
            log_message(f"\n--- [사이클 {cycle_count}] 전송 작업을 시작합니다 ---")
            if not activate_kakaotalk():
                log_message("[경고] 카카오톡 메인 창을 찾지 못했습니다.")
            
            success_count = 0
            for index, room in enumerate(rooms):
                if not is_running: break
                activate_kakaotalk()
                time.sleep(0.5)
                try:
                    log_message(f"[{room}] 검색 및 진입 시도 중...")
                    pyautogui.hotkey('ctrl', 'f')
                    time.sleep(delay)
                    if index > 0:
                        for _ in range(15):
                            pyautogui.press('backspace')
                            time.sleep(0.05)
                        time.sleep(0.2)
                    pyperclip.copy(room)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(delay)
                    pyautogui.press('down')
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    time.sleep(delay)
                    pyperclip.copy(message)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    time.sleep(delay)
                    pyautogui.hotkey('ctrl', 'w')
                    time.sleep(0.4)
                    success_count += 1
                    log_message(f"[{room}] 전송 완료! ({success_count}/{len(rooms)})")
                except Exception as e:
                    log_message(f"[에러] {room} 전송 실패: {e}")
            
            if is_running:
                activate_kakaotalk()
                pyautogui.press('esc')
                time.sleep(0.2)
                pyautogui.press('esc')
                log_message("[시스템] 모든 방 전송이 완료되었습니다.")
            
            if not is_repeat or not is_running:
                log_message("[완료] 모든 작업이 끝났습니다.")
                break
                
            log_message(f"[대기] 설정된 {interval_min}분 동안 대기합니다...")
            wait_seconds = interval_min * 60
            for _ in range(int(wait_seconds)):
                if not is_running: break
                time.sleep(1)
            cycle_count += 1
    finally:
        is_running = False
        if 'root_main' in globals():
            root_main.after(0, stop_process_ui)

def start_process():
    global is_running
    if is_running:
        messagebox.showwarning("경고", "이미 전송 작업 중입니다!")
        return
    rooms_raw = text_rooms.get("1.0", tk.END).strip()
    message = text_msg.get("1.0", tk.END).strip()
    if not rooms_raw or not message:
        messagebox.showwarning("경고", "대화방 목록과 메시지를 입력해 주세요!")
        return
    rooms = [r.strip() for r in rooms_raw.split('\n') if r.strip()]
    try: delay = float(entry_delay.get())
    except: delay = 1.0
    try: interval_min = float(entry_interval.get())
    except: interval_min = 1.0
    repeat_mode = var_repeat.get()
    
    is_running = True
    btn_start.config(state="disabled", bg="#94a3b8", fg="white")
    btn_stop.config(state="normal", bg="#ef4444", fg="white")
    text_log.config(state="normal")
    text_log.delete("1.0", tk.END)
    text_log.config(state="disabled")
    log_message("[시작] 자동 전송 스레드가 시작되었습니다.")
    threading.Thread(target=run_sending_loop, args=(rooms, message, delay, interval_min, repeat_mode), daemon=True).start()

def stop_process():
    global is_running
    is_running = False
    log_message("[중지] 사용자에 의해 중지되었습니다.")

def stop_process_ui():
    btn_start.config(state="normal", bg=PRIMARY_COLOR, fg="white")
    btn_stop.config(state="disabled", bg="#e2e8f0", fg=TEXT_SUB)

def start_main_program():
    global root_main, text_rooms, text_msg, entry_delay, entry_interval, var_repeat, btn_start, btn_stop, text_log
    root_main = tk.Tk()
    root_main.title("이상봇 베타버전")
    root_main.geometry("540x800")
    root_main.config(bg=BG_COLOR)
    root_main.resizable(False, False)

    # 상단 공지/문의 영역
    lbl_info = tk.Label(root_main, text="💡 문의 또는 피드백은 옾챗 '이상갠'으로 편하게 연락주세요!", fg=PRIMARY_COLOR, bg="#e0e7ff", font=("Pretendard", 10, "bold"), pady=8)
    lbl_info.pack(fill="x", padx=20, pady=(15, 10))

    # 입력 섹션 (대화방)
    tk.Label(root_main, text="대화방 목록 (엔터로 구분하여 여러 개 입력)", fg=TEXT_MAIN, bg=BG_COLOR, font=("Pretendard", 10, "bold")).pack(anchor="w", padx=20)
    text_rooms = scrolledtext.Text(root_main, width=58, height=5, font=("Pretendard", 10), bd=1, relief="solid")
    text_rooms.pack(padx=20, pady=(4, 10))

    # 입력 섹션 (메시지)
    tk.Label(root_main, text="보낼 메시지 내용", fg=TEXT_MAIN, bg=BG_COLOR, font=("Pretendard", 10, "bold")).pack(anchor="w", padx=20)
    text_msg = scrolledtext.Text(root_main, width=58, height=5, font=("Pretendard", 10), bd=1, relief="solid")
    text_msg.pack(padx=20, pady=(4, 10))

    # 설정 프레임 (카드 스타일)
    frame_setting = tk.LabelFrame(root_main, text=" 전송 상세 설정 ", fg=TEXT_MAIN, bg=CARD_BG, font=("Pretendard", 10, "bold"), padx=15, pady=10, bd=1, relief="solid")
    frame_setting.pack(pady=5, padx=20, fill="x")

    tk.Label(frame_setting, text="동작 딜레이 (초):", bg=CARD_BG, fg=TEXT_SUB, font=("Pretendard", 9)).grid(row=0, column=0, sticky="w", pady=4)
    entry_delay = tk.Entry(frame_setting, width=12, font=("Pretendard", 9), bd=1, relief="solid")
    entry_delay.insert(0, "1.0")
    entry_delay.grid(row=0, column=1, sticky="w", padx=10, pady=4)

    tk.Label(frame_setting, text="반복 간격 (분):", bg=CARD_BG, fg=TEXT_SUB, font=("Pretendard", 9)).grid(row=1, column=0, sticky="w", pady=4)
    entry_interval = tk.Entry(frame_setting, width=12, font=("Pretendard", 9), bd=1, relief="solid")
    entry_interval.insert(0, "5")
    entry_interval.grid(row=1, column=1, sticky="w", padx=10, pady=4)

    var_repeat = tk.BooleanVar(value=False)
    chk_repeat = tk.Checkbutton(frame_setting, text="일정 시간(분) 간격으로 자동 반복 전송 사용", variable=var_repeat, bg=CARD_BG, fg=TEXT_MAIN, font=("Pretendard", 9), activebackground=CARD_BG)
    chk_repeat.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

    # 버튼 프레임
    frame_btn = tk.Frame(root_main, bg=BG_COLOR)
    frame_btn.pack(pady=12, padx=20, fill="x")

    btn_start = tk.Button(frame_btn, text="전송 시작", bg=PRIMARY_COLOR, fg="white", font=("Pretendard", 11, "bold"), command=start_process, width=23, height=2, bd=0, cursor="hand2")
    btn_start.pack(side="left", padx=(0, 5))

    btn_stop = tk.Button(frame_btn, text="작업 중지", bg="#e2e8f0", fg=TEXT_SUB, font=("Pretendard", 11, "bold"), command=stop_process, width=23, height=2, bd=0, state="disabled", cursor="hand2")
    btn_stop.pack(side="right", padx=(5, 0))

    # 로그 모니터링 섹션
    tk.Label(root_main, text="실시간 전송 현황 모니터링", fg=TEXT_MAIN, bg=BG_COLOR, font=("Pretendard", 10, "bold")).pack(anchor="w", padx=20, pady=(2, 0))
    text_log = scrolledtext.Text(root_main, width=58, height=7, bg="#0f172a", fg="#4ade80", font=("Consolas", 9), bd=0)
    text_log.pack(padx=20, pady=(4, 15))
    text_log.config(state="disabled")

    root_main.mainloop()

if __name__ == "__main__":
    init_root = tk.Tk()
    app = LicenseApp(init_root)
    init_root.mainloop()
