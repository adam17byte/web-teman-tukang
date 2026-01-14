import math

def get_pagination_params(request, default_limit=10, max_limit=50):
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", default_limit))
    except ValueError:
        page = 1
        limit = default_limit

    if page < 1:
        page = 1

    if limit < 1:
        limit = default_limit
    elif limit > max_limit:
        limit = max_limit

    offset = (page - 1) * limit
    return page, limit, offset


def build_pagination_meta(page, limit, total):
    total_pages = math.ceil(total / limit) if limit else 1
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages
    }
