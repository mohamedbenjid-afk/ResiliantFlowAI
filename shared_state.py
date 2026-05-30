from notion_client import Client

notion = Client(auth=os.environ["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"])

# IDs des 4 collections
DB_EQUIPEMENTS    = "f8c546b6-40b6-484c-b686-6a6ad42520ee"
DB_OF             = "6777a9e0-4c76-49ca-a3d4-fb20a579cb2d"
DB_MAINTENANCE    = "1c9d8c5d-e394-490a-b913-e0cf833abb5b"
DB_STOCK          = "7229437a-027a-440f-a7be-5e37157f3b8d"

def get_equipement(nom):
    res = notion.databases.query(
        database_id=DB_EQUIPEMENTS,
        filter={"property": "Équipement", "title": {"equals": nom}}
    )
    return res["results"][0] if res["results"] else None

def get_of_actifs(equipement):
    res = notion.databases.query(
        database_id=DB_OF,
        filter={"and": [
            {"property": "Équipement concerné", "rich_text": {"contains": equipement}},
            {"property": "Statut", "select": {"equals": "En cours"}}
        ]}
    )
    return res["results"]

def get_stock_composant(nom):
    res = notion.databases.query(
        database_id=DB_STOCK,
        filter={"property": "Composant", "title": {"contains": nom}}
    )
    return res["results"][0] if res["results"] else None

def get_prochaine_maintenance(equipement):
    res = notion.databases.query(
        database_id=DB_MAINTENANCE,
        filter={"and": [
            {"property": "Équipement", "rich_text": {"contains": equipement}},
            {"property": "Statut", "select": {"equals": "Planifiée"}}
        ]},
        sorts=[{"property": "Date planifiée", "direction": "ascending"}]
    )
    return res["results"][0] if res["results"] else None
