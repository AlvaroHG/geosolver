import networkx as nx
from geosolver.diagram.get_instances import get_all_instances, get_instances
from geosolver.diagram.states import GeneralGraphParse
from geosolver.match.label_distances import label_distance_to_line, label_distance_to_point, label_distance_to_arc, \
    label_distance_to_angle
from geosolver.match.states import MatchParse
from geosolver.ontology import basic_ontology
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.ontology.states import TempFormula, Constant

__author__ = 'minjoon'



def parse_match_from_known_labels(general_graph_parse, known_labels):
    """
    There are only a few types:
    point
    line
    arc
    angle angle
    length line


    :param general_graph_parse:
    :param known_labels: [{'x':96, 'y':110, 'label': 'O', 'type': 'point'}, ]
    :return:
    """
    assert isinstance(general_graph_parse, GeneralGraphParse)
    label_strings = set()
    formulas = {}
    graph = nx.Graph()
    offset = general_graph_parse.graph_parse.image_segment_parse.diagram_image_segment.offset
    for idx, d in enumerate(known_labels):
        x = d['x'] - offset[0]
        y = d['y'] - offset[1]
        label_point = instantiators['point'](x, y)
        label = d['label']
        type_ = d['type']
        arr = type_.split(' ')
        if len(arr) > 1:
            type_ = arr[-1]

        # Find closest type_ instance's key in graph_parse
        instances = get_all_instances(general_graph_parse.graph_parse, type_)
        if len(arr) > 1 and type_ == 'line' and arr[0] == 'length':
            distances = [(key, label_distance_to_line(label_point, instance, True)) for key, instance in instances.iteritems()]
        elif type_ == 'line':
            distances = [(key, label_distance_to_line(label_point, instance, False)) for key, instance in instances.iteritems()]
        elif type_ == 'point':
            distances = [(key, label_distance_to_point(label_point, instance)) for key, instance in instances.iteritems()]
        elif type_ == 'arc':
            distances = [(key, label_distance_to_arc(label_point, instance)) for key, instance in instances.iteritems()]
        elif type_ == 'angle':
            distances = [(key, label_distance_to_angle(label_point, instance)) for key, instance in instances.iteritems()]

        # Then use the key to get general instance in general graph
        # Wrap the general instance in formula. If there are extra prefixes, add these as well the formula
        argmin_key = min(distances, key=lambda pair: pair[1])[0]
        if type_ == 'line':
            a_key, b_key = argmin_key
            line = general_graph_parse.line_graph[a_key][b_key]['instance']
            constant = Constant(line, basic_ontology.types['line'])
            formula = TempFormula(basic_ontology, constant, [])
            if len(arr) > 1 and arr[0] == 'length':
                formula = TempFormula(basic_ontology, basic_ontology.functions['lengthOf'], [formula])
        elif type_ == 'point':
            point = general_graph_parse.intersection_points[argmin_key]
            constant = Constant(point, basic_ontology.types['point'])
            formula = TempFormula(basic_ontology, constant, [])
        elif type_ == 'angle':
            assert len(arr) > 1 and arr[0] == 'angle'
            angle = get_instances(general_graph_parse, type_, *argmin_key).values()[0]
            constant = Constant(angle, basic_ontology.types['angle'])
            formula = TempFormula(basic_ontology, constant, [])
            formula = TempFormula(basic_ontology, basic_ontology.functions['angleOf_angle'], [formula])
        elif type_ == 'arc':
            (center_key, radius_key), a_key, b_key = argmin_key
            arc = general_graph_parse.arc_graphs[(center_key, radius_key)][a_key][b_key]['instance']
            constant = Constant(arc, basic_ontology.types['arc'])
            formula = TempFormula(basic_ontology, constant, [])

        # add edge between label and formula
        formulas[('formula', idx)] = formula
        label_strings.add(label)
        graph.add_edge(label, ('formula', idx))

    match_parse = MatchParse(general_graph_parse, label_strings, formulas, graph)
    return match_parse