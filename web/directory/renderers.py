from rest_framework.renderers import BaseRenderer
import csv
from io import StringIO

class CSVRenderer(BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, media_type=None, renderer_context=None):
        if data is None:
            return ''

        csv_file = StringIO()
        writer = csv.writer(csv_file)

        # If the data contains a list of items, we expect a list of dictionaries
        # after serializer has done its work. First, write the header with field names.
        if isinstance(data, list) and len(data) > 0:
            writer.writerow(data[0].keys())

        for item in data:
            writer.writerow(item.values())

        return csv_file.getvalue()
