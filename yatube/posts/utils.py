from django.core.paginator import Paginator


def get_page_context(request, post_list, per_page):
    paginator = Paginator(post_list, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
