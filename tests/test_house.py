from src.house import get_house_by_property

class Args:

    def __init__(self, map):
        self.map = map

    def get(self, key, *args, **kwargs):
        default = None
        if args:
            default = args[0]
        return self.map.get(key, default)

def test_get_house_by_property(app):
    args = Args({
        "status": "for_sale",
    })
    houses = get_house_by_property(args)
    assert [h.id for h in houses.items] == ["hash1", "hash2"]
