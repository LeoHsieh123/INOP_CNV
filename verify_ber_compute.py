import math

def ber_compute_confidence_level(errors, bits, ber_target,logger=None):

    step1 = 0
    for k in range(0, errors + 1):
        try:
            term = pow((bits * float(ber_target)), k) / math.factorial(k)
            step1 += term
        except OverflowError:
            # Handle potential overflow for large numbers
            message = 'Warning: OverflowError detected during BER confidence level calculation.'
            if logger:
                logger.warning(message)
            else:
                print(message)
            break
    # Final confidence level calculation
    step2 = (1 - (step1 * math.exp(-bits * float(ber_target)))) * 100

    return float('{0:.1f}'.format(step2))

if __name__ == '__main__':
    print("--- BER 信賴區間計算機 ---")

    try:
        total_bits = 0
        while True:
            choice = input("\n請選擇總位元數的計算方式 (1: 依速率和時間計算, 2: 依封包數量計算): ")
            if choice in ['1', '2']:
                break
            else:
                print("無效的選擇，請重新輸入 1 或 2。")

        if choice == '1':
            # --- 方法1: 依速率和時間計算 ---
            print("\n--- 請輸入速率和時間 ---")
            speed_gbps = float(input("請輸入速率 (Speed) (單位: Gbps): "))
            measurement_time_sec = float(input("請輸入測量時間 (Measurement time) (單位: 秒): "))
            # 總位元數 = 速率 (bits per second) * 時間 (seconds)
            total_bits = speed_gbps * 1e9 * measurement_time_sec
        
        elif choice == '2':
            # --- 方法2: 依封包數量計算 ---
            print("\n--- 請輸入封包資訊 ---")
            packet_count = int(input("請輸入總封包數量 (Total packet count): "))
            packet_size_bytes = int(input("請輸入每個封包的大小 (Packet size) (單位: Bytes): "))
            # 總位元數 = 封包數量 * 每個封包的大小 (bytes) * 8
            total_bits = packet_count * packet_size_bytes * 8

        # --- 輸入共通參數 ---
        print("\n--- 請輸入共通測試參數 ---")
        test_errors = int(input("請輸入量測到的錯誤位元數 (Number of measured bit errors): "))
        test_ber_target = float(input("請輸入指定的 BER 目標 (Specified BER) (例如: 1e-12): "))

        # --- 計算信賴區間 ---
        confidence = ber_compute_confidence_level(test_errors, total_bits, test_ber_target)

        # --- 顯示結果 ---
        print(f"\n--- BER 信賴區間驗證結果 ---")
        print(f"輸入的錯誤位元數: {test_errors}")
        print(f"計算的總位元數: {total_bits:.2e}")
        print(f"指定的 BER 目標: {test_ber_target}")
        print(f"-----------------------------------------")
        print(f"計算出的信賴區間: {confidence}%")

    except ValueError:
        print("\n錯誤：輸入的格式不正確，請確認您輸入的是有效的數字。")
    except Exception as e:
        print(f"\n計算過程中發生錯誤: {e}")
