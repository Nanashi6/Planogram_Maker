import pandas as pd
from DataLayer.shemas import Category, Brand, Product, ShelfUnit, Shelf, Planogram, PlacedProduct
from DataLayer.dao import CategoryDAO, BrandDAO, ProductDAO, ShelfUnitDAO, ShelfDAO, PlanogramDAO, PlacedProductDAO
from DataLayer.enums import SegmentEnum, RatingEnum

segments = {
    'Премиальный': SegmentEnum.PREMIUM,
    'Средний': SegmentEnum.MIDDLE,
    'Бюджетный': SegmentEnum.BUDGET,
    '-': SegmentEnum.NONE
}
ratings = {
    '1': RatingEnum.ONE,
    '2': RatingEnum.TWO,
    '3': RatingEnum.THREE,
    '4': RatingEnum.FOUR,
    '5': RatingEnum.FIVE,
    '6': RatingEnum.SIX,
    '7': RatingEnum.SEVEN,
    '8': RatingEnum.EIGHT,
    '9': RatingEnum.NINE,
    '10': RatingEnum.TEN,
    '-': RatingEnum.NONE
}

def init():
    if not CategoryDAO.get_all():
        init_categories()
    if not BrandDAO.get_all():
        init_brands()
    if not ProductDAO.get_all():
        init_products()
    if not ShelfUnitDAO.get_all():
        init_shelfUnits()
    if not ShelfDAO.get_all():
        init_shelves()
    # if not PlanogramDAO.get_all():
    #     init_planograms()
    # if not PlacedProductDAO.get_all():
    #     init_placedProducts()
    else:
        print("INFO: skipping DB initialization.")

# FIXME Сделать универсальные методы (для загрузки из указанного, а не фиксированного иссточника)

def init_categories(df = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Исходные данные (Автохимия).xlsx", sheet_name='Лист2')):    
    unique_indices = df.drop_duplicates(subset=['Категория'], keep='first').index.to_list()
    categories = [Category(name=ser['Категория']) for ind, ser in df.loc[unique_indices].iterrows()]    
    CategoryDAO.add_many(categories)

def init_brands(df = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Исходные данные (Автохимия).xlsx", sheet_name='Лист2')):
    unique_indices = df.drop_duplicates(subset=['Бренд'], keep='first').index.to_list()
    brands = [Brand(
        name=ser['Бренд'],
        rating=ratings[str(ser['Рейтинг бренда'])]
    ) for ind, ser in df.loc[unique_indices].iterrows()]
    BrandDAO.add_many(brands)

def init_products(df = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Исходные данные (Автохимия).xlsx", sheet_name='Лист2'), 
                  df2 = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Исходные данные (Автохимия).xlsx", sheet_name='Характеристики товаров')):
    products = [Product(
        segment=segments[ser['Сегмент']],
        name=ser['Наименование товара (SKU)'],
        barcode=ser['Штрихкод'],
        SKU_rating=ratings[str(ser['Рейтинг SKU'])],
        length=df2[df2['Штрихкод'] == ser['Штрихкод']]['Длина, см.'],
        depth=df2[df2['Штрихкод'] == ser['Штрихкод']]['Ширина, см.'],
        height=df2[df2['Штрихкод'] == ser['Штрихкод']]['Высота, см.'],
        weight=df2[df2['Штрихкод'] == ser['Штрихкод']]['Масса, кг.'],
        price=df2[df2['Штрихкод'] == ser['Штрихкод']]['Цена, руб.'],
        brand_id=BrandDAO.get_one(Brand(name=ser['Бренд'])).id,
        category_id=CategoryDAO.get_one(Category(name=ser['Категория'])).id
    ) for ind, ser in df.iterrows()]
    ProductDAO.add_many(products)

def init_shelfUnits(df = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Исходные данные (Автохимия).xlsx", sheet_name='Характеристики стеллажа')):
    unique_indices = df.drop_duplicates(subset=['Номер стеллажа'], keep='first').index.to_list()
    shelfUnits = [ShelfUnit(shelf_unit_number=ser['Номер стеллажа']) for ind, ser in df.loc[unique_indices].iterrows()]
    ShelfUnitDAO.add_many(shelfUnits)

def init_shelves(df = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Исходные данные (Автохимия).xlsx", sheet_name='Характеристики стеллажа')):
    shelves = [Shelf(shelf_number=ser['Номер полки'], 
                         length=ser['Длина, см'], 
                         depth=ser['Глубина, см'], 
                         height=ser['Расстояние до вышестоящей полки, см'], 
                         max_weight=ser['Допустимая нагрузка, кг'], 
                         shelf_unit_id=ShelfUnitDAO.get_one(ShelfUnit(shelf_unit_number=ser['Номер стеллажа'])).id,
                        ) for ind, ser in df.iterrows()]
    ShelfDAO.add_many(shelves)

# def init_planograms():
#     planogram = Planogram(name='test', shelf_unit_id=ShelfUnitDAO.get_all().pop().id)
#     PlanogramDAO.add(planogram)

# def init_placedProducts(df = pd.read_excel("C:/Users/Yury Youzhanka/Desktop/DiplomaData/Автохимия апрель 2024.xlsx", sheet_name='Вертикально')):
#     placed_products = []
#     for i in range(1,5):
#         for ind, row in df[i].dropna().items():
#             placed_products.append(PlacedProduct(shelf_id=ShelfDAO.get_one(Shelf(shelf_number=i)).id,
#                                                      product_id=ProductDAO.get_one(Product(name=row)).id,
#                                                      planogram_id=PlanogramDAO.get_all()[0].id,
#                                                      position=ind))
#     PlacedProductDAO.add_many(placed_products)