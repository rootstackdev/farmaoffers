try:
    # funciona en muchas versiones
    from odoo.addons.http_routing.models.ir_http import slug  # type: ignore
except Exception:
    from odoo.tools import ustr
    import re, unicodedata

    def _slugify(text):
        s = ustr(text or "").strip().lower()
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        s = re.sub(r"[\s_]+", "-", s)
        s = re.sub(r"[^a-z0-9\-]", "", s)
        return re.sub(r"-{2,}", "-", s).strip("-")

    def slug(value):
        # Si es un recordset: nombre + id (como hace Odoo)
        name = getattr(value, "display_name", None)
        rid = getattr(value, "id", None)
        if name and rid:
            return f"{_slugify(name)}-{rid}"
        return _slugify(value)
