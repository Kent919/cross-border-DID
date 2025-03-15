from Crypto.PublicKey import RSA
from contracts.smart_contract import CrossBorderContract
import json

class BCAIdentity:
    def __init__(self, user_id):
        self.user_id = user_id
        self.key_pair = RSA.generate(2048)
        self.public_key = self.key_pair.publickey().export_key()
        self.contract = CrossBorderContract()
    
    def register(self):
        """将身份注册到智能合约"""
        success, message = self.contract.register_identity(
            self.user_id, 
            self.public_key.decode()
        )
        if success:
            print(f"✅ 注册成功 | 用户ID: {self.user_id}")
            print(f"公钥: {self.public_key[:50]}...")
        else:
            print(f"❌ 注册失败: {message}")
        return success
    
    def simulate_verification(self):
        """模拟验证流程"""
        # 生成示例签名（实际应使用私钥签名）
        mock_signature = "mock_sig_" + self.user_id[-4:]
        success, message = self.contract.verify_identity(
            self.user_id, 
            mock_signature
        )
        print(f"\n验证结果: {'✅ 成功' if success else '❌ 失败'}")
        print(f"详细信息: {message}")
        return success

# 示例运行
if __name__ == "__main__":
    # 创建澳门车主身份
    driver = BCAIdentity("macau_driver_8899")
    
    # 执行注册
    if driver.register():
        # 执行验证
        driver.simulate_verification()
