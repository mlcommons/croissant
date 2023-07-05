import iso639

class JSONParser:
    def __init__(self, data):
        self.data = data

    def parse_json(self):
        name = self.data.get('name', '')
        description = self.data.get('description', '')
        url = self.data.get('url', '')
        keywords = self.data.get('keywords', '')
        language = self.parse_language()
        license = self.data.get('license', '')
        citation = self.data.get('citation', '')
        return name, description, url, keywords, language, license, citation
    
    def parse_records(self):
        records = self.data.get('recordSet')
        categories = {}
        if records:
            for record in records:
                category = record.get('name')
                description = record.get('description')
                fields = record.get('field')
                columns = {}
                for field in fields:
                    field_names = field.get('name')
                    data_types = field.get('dataType')
                    columns[field_names] = data_types
                categories[category] = {'description': description, 'columns': columns}
            return categories
        else:
            return {}
    
    def parse_language(self):
        language_code = self.data.get('@language')
        if language_code:
             language = iso639.languages.get(alpha2=language_code)
             return language.name
        else:
            return language_code
