"""Własne wyjątki aplikacji"""


class StudioError(Exception):
    """Bazowy wyjątek aplikacji"""


class DataLoadError(StudioError):
    """Nie udało się wczytać pliku CSV"""


class ValidationError(StudioError):
    """Niepoprawne parametry operacji lub wybór kolumn"""