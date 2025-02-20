class UserCookieMiddleWare:
    """
    Middleware to set user cookie
    If user is authenticated and there is no cookie, set the cookie,
    If the user is not authenticated and the cookie remains, delete it
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and not request.COOKIES.get('isLoggedIn'):
            response.set_cookie("isLoggedIn", 'true')
        elif not request.user.is_authenticated and request.COOKIES.get('isLoggedIn'):
            #else if if no user and cookie remove user cookie, logout
            response.delete_cookie("isLoggedIn")
        return response
