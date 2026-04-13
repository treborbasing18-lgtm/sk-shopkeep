class Validators: 
    @staticmethod 
    def validate_username(username): 
        if not username or len(username) < 3: 
            return False, "Username must be at least 3 characters" 
        return True, None 
    
    @staticmethod 
    def validate_password(password): 
        if not password or len(password) < 6: 
            return False, "Password must be at least 6 characters" 
        return True, None 
