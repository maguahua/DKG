import json
import random
import time
from datetime import datetime

import base58
import pandas as pd

import threshold_crypto as tc

n = 34
t = 18
curve_params = tc.CurveParameters()
thresh_params = tc.ThresholdParameters(t=t, n=n)


# def draw_line_graph(filename, title, index_x, index_y):
#     df = pd.read_csv(filename)
#
#     plt.plot(df['elapse_time'])
#     plt.title(title)
#     plt.xlabel(index_x)
#     plt.ylabel(index_y)
#
#     plt.savefig(title + '.png')


def DPKG(curve_params, thresh_params, participant_ids):
    participants = [tc.Participant(id, participant_ids, curve_params, thresh_params) for id in participant_ids]
    for pi in participants:
        for pj in participants:
            if pj != pi:
                closed_commitment = pj.closed_commmitment()
                pi.receive_closed_commitment(closed_commitment)
    for pi in participants:
        for pj in participants:
            if pj != pi:
                open_commitment = pj.open_commitment()
                pi.receive_open_commitment(open_commitment)
    public_key = participants[0].compute_public_key()
    for pk in [p.compute_public_key() for p in participants[1:]]:
        assert public_key == pk
    for pi in participants:
        for pj in participants:
            if pj != pi:
                F_ij = pj.F_ij_value()
                pi.receive_F_ij_value(F_ij)
    for pi in participants:
        for pj in participants:
            if pj != pi:
                s_ij = pj.s_ij_value_for_participant(pi.id)
                pi.receive_sij(s_ij)
    shares = [p.compute_share() for p in participants]
    return public_key, shares


pub_key, key_shares = tc.create_public_key_and_shares_centralized(curve_params, thresh_params)
participant_ids = list(range(1, thresh_params.n + 1))

# DPKG执行次数，多次实验求平均值可以得到一个比较稳定的时间开销（一次大约20s左右，可以适当的选择参数）
# DPKG_times = 1
# elapse_times_list = []
# for i in range(DPKG_times):
#     start_time = time.time()
#     pub_key, key_shares = DPKG(curve_params, thresh_params, participant_ids)
#
#     # 生成审计密钥文件
#     # df = pd.DataFrame()
#     # df['aud_pk'] = [(int(pub_key.Q.x), int(pub_key.Q.y))] * 34
#     # df['aud_sk'] = ["'" + str(share.y) for share in key_shares]
#     # df.to_csv(f'aud_key{DPKG_times}.csv', index=False)
#
#     end_time = time.time()
#     elapse_time = end_time - start_time
#     elapse_times_list.append(elapse_time)
#     print(f"第{i}次执行了{elapse_time}秒")
#     # print(f"{DPKG_times} times Key Gen time(s):", end_time - start_time)

# df = pd.DataFrame()
# df['elapse_time'] = elapse_times_list
# df.to_csv('DPKG_data.csv')

# draw_line_graph('DPKG_data.csv', 'DPKG_data', 'index', 'time')

with open("vc_test.json", "r") as file:
    vcdemo = json.load(file)

# 交易凭证的例子，因为仅与加密内容相关，因此买家和买家都用了同一个vc
transaction_cred = {"Buyer": vcdemo, "Seller": vcdemo, "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:19],
                    "transaction_amount": 99999999.99}
json_str = json.dumps(transaction_cred)
bytes_data = json_str.encode("utf-8")
base58_encoded = base58.b58encode(bytes_data)
base58_encoded_str = base58_encoded.decode('utf-8')

# 加密执行次数，多次实验求平均值可以得到一个比较稳定的时间开销
Enc_times = 100
enc_elapse_times_list = []

for i in range(Enc_times):
    start_time = time.time()
    encrypted_message = tc.encrypt_message(base58_encoded_str, pub_key)
    end_time = time.time()
    elapse_time = end_time - start_time
    enc_elapse_times_list.append(elapse_time)
    print(f"第{i}次加密执行了{elapse_time}秒。")

dec_df = pd.DataFrame()
dec_df['elapse_time'] = enc_elapse_times_list
dec_df.to_csv('Enc_data.csv')

# 解密执行次数，多次实验求平均值可以得到一个比较稳定的时间开销
Dec_times = 100
dec_elapse_times_list = []

for i in range(Dec_times):
    start_time = time.time()
    partial_decryptions = []
    for i in random.sample(range(n), t):
        participant_share = key_shares[i]
        partial_decryption = tc.compute_partial_decryption(encrypted_message, participant_share)
        partial_decryptions.append(partial_decryption)
    decrypted_message = tc.decrypt_message(partial_decryptions, encrypted_message, thresh_params)
    end_time = time.time()
    elapse_time = end_time - start_time
    dec_elapse_times_list.append(elapse_time)
    print(f"第{i}次解密执行了{elapse_time}秒。")

dec_df = pd.DataFrame()
dec_df['elapse_time'] = dec_elapse_times_list
dec_df.to_csv('Dec_data.csv')
