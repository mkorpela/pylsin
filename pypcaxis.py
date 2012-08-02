import re
from itertools import product
from operator import mul


class Dimension(object):

    def __init__(self, title, values):
        self.title = title
        self.values = values

    def __len__(self):
        return len(self.values)


class Table(object):

    def __init__(self, dimensions=None, data=None):
        self.dimensions = dimensions or []
        self.data = data or []

    def add_dimension(self, dimension):
        self.dimensions.append(dimension)

    def get_by(self, title, value):
        return TableWithFixedDimension(self, title, value)

    def get(self, *criteria):
        dim_lenghts = [len(dim) for dim in self.dimensions]
        dim_indices = [dim.values.index(c) for (dim, c)
                       in zip(self.dimensions, criteria)]
        return self.data[sum(reduce(mul, dim_lenghts[i+1:], 1) * index
                         for i, index in enumerate(dim_indices))]


class TableWithFixedDimension(Table):

    def __init__(self, table, fixed_dimension_title, fixed_dimension_value):
        self._table = table
        self._fixed_dimension_value = fixed_dimension_value
        self._fixed_dimension_index = [dim.title for dim in self._table.dimensions].index(fixed_dimension_title)
        dimensions = self._table.dimensions[:]
        dimensions.pop(self._fixed_dimension_index)
        Table.__init__(self, dimensions)

    def get(self, *criteria):
        criteria = criteria[:self._fixed_dimension_index]+(self._fixed_dimension_value,)+criteria[self._fixed_dimension_index:]
        return self._table.get(*criteria)


def parse(path):
    data = read_data(path)
    value_regex = re.compile(r'VALUES\(\"(.*)\"\)')
    table = Table()
    for item in data:
        if not item:
            continue
        name, values = [t.strip() for t in item.split('=', 1)]
        value_match = value_regex.match(name)
        if value_match:
            title = value_match.group(1)
            table.add_dimension(create_dimension(title, values))
        if name == 'DATA':
            table.data = [data_object(i) for i in values.split(' ')]
    return table


def read_data(path):
    return [t.strip() for t in
            open(path).read().decode('ISO-8859-1').split(';')]


def data_object(data_text):
    data_text = data_text.strip()
    if not data_text:
        return data_text
    if '"' == data_text[0]:
        return data_text[1:-1]
    try:
        return int(data_text)
    except ValueError:
        try:
            return float(data_text)
        except ValueError:
            return data_text


def create_dimension(title, values):
    # values are defined like: "foo","bar","zap"
    values = values.replace('\r\n', '')[1:-1].split('","')
    return Dimension(title, values)


if __name__ == '__main__':
    table = parse('examples/tulot.px')
    assert table.get('2008', 'Tuusula - Tusby', 'Veronalaiset tulot, mediaani') == 26240.375
    assert table.get('2009', 'Tuusula - Tusby', 'Veronalaiset tulot, mediaani') == 26877.565
    for vuosi in ('2005', '2006', '2007', '2008', '2009'):
        assert table.get(vuosi, 'Koko maa', 'Tulonsaajia') == \
                 table.get_by('Vuosi', vuosi).get('Koko maa', 'Tulonsaajia')
        assert table.get(vuosi, 'Koko maa', u'Tulot miinus verot keskim\xe4\xe4rin') == \
                         table.get_by('Vuosi', vuosi).get('Koko maa', u'Tulot miinus verot keskim\xe4\xe4rin')
    assert table.get('2009', u'\xc4\xe4nekoski', u'Tulot miinus verot keskim\xe4\xe4rin') == \
                  table.get_by('Vuosi', '2009').get(u'\xc4\xe4nekoski', u'Tulot miinus verot keskim\xe4\xe4rin')
    assert table.get('2007', u'Hyvink\xe4\xe4 - Hyvinge', 'Tulonsaajia') == \
           table.get_by('Vuosi', '2007').get(u'Hyvink\xe4\xe4 - Hyvinge', 'Tulonsaajia')
    assert table.get('2008', 'Tuusula - Tusby', 'Veronalaiset tulot, mediaani') == \
           table.get_by('Kunta', 'Tuusula - Tusby').get_by('Vuosi', '2008').get('Veronalaiset tulot, mediaani')
    table = parse('examples/vaalit.px')
    assert table.get('Uudenmaan vaalipiiri', 'VIHR', u'Yhteens\xe4', u'78 vuotta') == '-'
