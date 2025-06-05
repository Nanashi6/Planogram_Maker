import enum

class SegmentEnum(str, enum.Enum):
    PREMIUM = "Премиальный"
    MIDDLE = "Средний"
    BUDGET = "Бюджетный"
    NONE = "-"

class RatingEnum(str, enum.Enum):
    ONE = '1'
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = '10'
    NONE = '-'

    def to_int(self) -> int:
        if self == RatingEnum.NONE:
            return 0
        else:
            return int(self.value)
        
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