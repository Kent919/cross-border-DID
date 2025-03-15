from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

class ABEProcessor:
    def __init__(self):
        self.master_key = get_random_bytes(32)  # 256-bit密钥
    
    def encrypt_data(self, plaintext, policy):
        cipher = AES.new(self.master_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(cipher.nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "policy": policy
        }
    
    def decrypt_data(self, encrypted_data):
        cipher = AES.new(self.master_key, AES.MODE_GCM,
                          nonce=base64.b64decode(encrypted_data["nonce"]))
        return cipher.decrypt_and_verify(
            base64.b64decode(encrypted_data["ciphertext"]),
            base64.b64decode(encrypted_data["tag"])
        ).decode()

# 示例用法
if __name__ == "__main__":
    processor = ABEProcessor()
    encrypted = processor.encrypt_data("跨境通行数据", {"required": ["A001", "A002"]})
    print("🔒 加密结果：", encrypted)
    decrypted = processor.decrypt_data(encrypted)
    print("🔓 解密结果：", decrypted)
