import enum

class BrandSorting(str, enum.Enum):
    NameAsc = "NameAsc"
    NameDesc = "NameDesc"
    RatingAsc = "RatingAsc"
    RatingDesc = "RatingDesc"

class ProductSorting(str, enum.Enum):
    PriceAsc = "PriceAsc"
    PriceDesc = "PriceDesc"
    RatingAsc = "RatingAsc"
    RatingDesc = "RatingDesc"
    NameAsc = "NameAsc"
    NameDesc = "NameDesc"