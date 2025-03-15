import json
from datetime import datetime
from pathlib import Path

class CrossBorderContract:
    def __init__(self):
        self.state_file = Path("src/data/contract_state.json")
        self.state = self._load_state()
    
    def _load_state(self):
        """加载合约状态"""
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "identities": {},
                "transactions": [],
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_state(self):
        """保存合约状态"""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def register_identity(self, user_id, public_key):
        """身份注册方法"""
        if user_id in self.state["identities"]:
            return False, "用户已存在"
        
        self.state["identities"][user_id] = {
            "public_key": public_key,
            "verified": False,
            "registration_time": datetime.now().isoformat()
        }
        self._record_transaction(f"REGISTER:{user_id}")
        self._save_state()
        return True, "注册成功"
    
    def verify_identity(self, user_id, signature):
        """身份验证方法"""
        if user_id not in self.state["identities"]:
            return False, "用户不存在"
        
        # 简化签名验证（实际应使用密码学库）
        identity = self.state["identities"][user_id]
        if len(signature) > 5:  # 示例验证逻辑
            identity["verified"] = True
            self._record_transaction(f"VERIFY_SUCCESS:{user_id}")
            self._save_state()
            return True, "验证成功"
        
        self._record_transaction(f"VERIFY_FAIL:{user_id}")
        return False, "签名无效"
    
    def _record_transaction(self, action):
        """记录交易日志"""
        self.state["transactions"].append({
            "action": action,
            "timestamp": datetime.now().isoformat()
        })

# 示例用法
if __name__ == "__main__":
    contract = CrossBorderContract()
    
    # 测试注册
    success, msg = contract.register_identity("macau_001", "pub_key_123")
    print(f"注册结果: {success} - {msg}")
    
    # 测试验证
    success, msg = contract.verify_identity("macau_001", "sig_456")
    print(f"验证结果: {success} - {msg}")
