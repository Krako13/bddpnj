# utils/security.py

def set_security_headers(response):
    csp = (
        "default-src 'self'; "  # Par défaut, autorise uniquement le contenu provenant de 'self'
        "script-src 'self' 'unsafe-inline' https://code.jquery.com https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com; "  
        "style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com https://fonts.googleapis.com; "  
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "  
        "img-src 'self' data:;"  # Autorise les images provenant de 'self' et les images en data URI
    )
    response.headers['Content-Security-Policy'] = csp
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
