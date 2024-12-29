import re

class InputValidation():

    def __init__(self):
        self.error_array = []
    
    def validate_mail(self,input: str) -> None:
        x = re.search("^\w+@\w+\.\w+", input)
        if not x:
            self.error_array.append( "Email error" )
            return ""
        return x.group()
    
    def validate_password(self, input: str) -> None:
        x = re.search("(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{10,}", input)
        if not x:
            self.error_array.append( "Password error" )
            return ""
        return x.group()

    def validate_phone(self, input: str) -> None:
        x = re.search("\d{7,16}", input)
        if not x:
            self.error_array.append( "Number error" )
            return ""
        return x.group()

    def validate_name(self, input: str) -> None:
        x = re.search("^\w+\s{1}\w+", input)
        if not x:
            self.error_array.append( "Name error" )
            return ""
        return x.group()

    def get_all(self) -> str:
        return "\n".join(self.error_array)

    def getfirst(self) -> str:
        if len(self.error_array) > 0:
            return self.error_array[0]
        else:
            return ""
        
    def count(self) -> int:
        return len( self.error_array )
    