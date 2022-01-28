from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    year = int(date.today().strftime("%Y"))
    return {
        'year': year
    }
