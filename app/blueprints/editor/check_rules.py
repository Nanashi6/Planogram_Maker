from DataLayer.dao import ProductDAO


def get_free_percentage(c_name, reply, shelf_number, shelf_id):
    return 100 - reply.rules.get_total_percentage_on_shelf(shelf_number, shelf_id, c_name)

def check_total_percentage(c_name, new_percentage, reply, shelf_number, shelf_id):
    free_percentage = get_free_percentage(c_name, reply, shelf_number, shelf_id)
    return False if free_percentage < new_percentage else True

def get_all_categories_for_shelf(reply, shelf_number, shelf_id):
    return reply.rules.get_all_categories_on_shelf(shelf_number, shelf_id)

def can_place_product(product, reply, shelf_number, shelf_id, shelf_len, pps):
    total_percentage_for_category = reply.rules.get_category_percentage_on_shelf(shelf_number, shelf_id, product.category.name)
    category_length = total_percentage_for_category * shelf_len / 100

    pps_len = 0
    for pp in pps:
        pproduct = ProductDAO.get_by_id(pp['product_id'])
        if pp['shelf_id'] == shelf_id:
            if pproduct.category.id == product.category.id:
                pps_len += pproduct.depth + 0.5           # 0.5

    return True if pps_len + product.depth <= category_length  else False
