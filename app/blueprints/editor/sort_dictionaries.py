from DataLayer.enums import BrandSorting, ProductSorting


p_sort_keys = {
    ProductSorting.PriceAsc:    "Цена по возрастанию",
    ProductSorting.PriceDesc:   "Цена по убыванию",
    ProductSorting.RatingAsc:   "Рейтинг по возрастанию",
    ProductSorting.RatingDesc:  "Рейтинг по убыванию",
    ProductSorting.NameAsc:     "Название (А-Я)",
    ProductSorting.NameDesc:    "Название (Я-А)",
}

b_sort_keys = {
    BrandSorting.NameAsc:    "Название бренда (А-Я)",
    BrandSorting.NameDesc:   "Название бренда (Я-А)",
    BrandSorting.RatingAsc:  "Рейтинг бренда (по возрастанию)",
    BrandSorting.RatingDesc: "Рейтинг бренда (по убыванию)",
}