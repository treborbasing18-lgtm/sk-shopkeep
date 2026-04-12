class Validators: 
    @staticmethod 
    def validate_username(username): 
        if not username or len(username) < 3: 
            return False, "Username must be at least 3 characters" 
        return True, None 
