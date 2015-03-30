# -*- coding: utf-8 -*-

"""
PrtgObject Models
"""

from copy import deepcopy
import logging
import re

from prtg.exceptions import BadTarget


INHERITED_PROPS = {'tags'}
LIST_TYPE_PROPS = {'tags'}

CONTENT_TYPE_ALL = 'all'
CONTENT_TYPES = ['groups', 'devices', 'sensors']


class PrtgObject(object):
    """
    PRTG base object.
    """

    changed = False
    content_type = 'prtg'
    objid = None

    column_table = {
        'all': [
            'objid', 'type', 'tags', 'active', 'name', 'status', 'parentid', 'result',
        ],
        'sensors': [
            'downtime', 'downtimetime', 'downtimesince', 'uptime', 'uptimetime', 'uptimesince', 'knowntime',
            'cumsince', 'sensor', 'interval', 'lastcheck', 'lastup', 'lastdown', 'device', 'group', 'probe',
            'grpdev', 'notifiesx', 'intervalx', 'access', 'dependency', 'probegroupdevice', 'status', 'message',
            'priority', 'lastvalue', 'upsens', 'downsens', 'downacksens', 'partialdownsens', 'warnsens',
            'pausedsens', 'unusualsens', 'undefinedsens', 'totalsens', 'favorite', 'schedule', 'minigraph', 'comments',
            'parentid'
        ],
        'devices': [
            'device', 'group', 'probe', 'grpdev', 'notifiesx', 'intervalx', 'access', 'dependency',
            'probegroupdevice', 'status', 'message', 'priority', 'upsens', 'downsens', 'downacksens',
            'partialdownsens', 'warnsens', 'pausedsens', 'unusualsens', 'undefinedsens', 'totalsens',
            'favorite', 'schedule', 'deviceicon', 'host', 'comments', 'icon', 'location', 'parentid'
        ],
        'groups': [
            'group', 'device', 'sensor'
        ],
        'status': [
            'NewMessages', 'NewAlarms', 'Alarms', 'AckAlarms', 'NewToDos', 'Clock', 'ActivationStatusMessage',
            'BackgroundTasks', 'CorrelationTasks', 'AutoDiscoTasks', 'Version', 'PRTGUpdateAvailable', 'IsAdminUser',
            'IsCluster', 'ReadOnlyUser', 'ReadOnlyAllowAcknowledge'
        ]
    }

    def __init__(self, **kwargs):
        self.type = str(self.__class__.__name__)
        for key in self.column_table['all']:
            try:
                value = kwargs[key]
                self.update_field(key, value)
            except KeyError:
                pass

    def update_field(self, key, value, inherited_values=None):
        if key == 'tags':  # Process tags as a list
            if isinstance(value, str):
                if value:
                    value = value.split(' ')
                else:
                    value = []
                if inherited_values:
                    value += inherited_values
        # This was commented out because we found non-integer ids.
        # if key == 'objid':
        #     value = int(value)
        # if key == 'parentid':
        #     value = int(value)
        self.__setattr__(key, value)

    def __repr__(self):
        return self.__class__.__name__ + str(vars(self))


# TODO: Generify these.
class Sensor(PrtgObject):
    """
    PRTG sensor object.
    """

    content_type = 'sensors'

    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['sensors']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Device(PrtgObject):
    """
    PRTG device object.
    """

    content_type = 'devices'

    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['devices']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Group(PrtgObject):
    """
    PRTG group object.
    """

    content_type = 'groups'

    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['groups']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Status(PrtgObject):
    """
    PRTG Status Object.
    """

    content_type = 'status'

    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['status']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


def _subtract_set_from_list(a_list, a_set_of_removals):
    return list(filter(lambda element: element not in a_set_of_removals, a_list))


def _get_entity_value(entity, prop, parent_value):
    """
    Gets the entity value, taking care of the tags not containing parent ones.
    :param entity: PRTG instance.
    :param prop: Property name.
    :param parent_value: Parent's property value.
    :return: PRTG instance's property own value.
    """
    entity_value = entity.__getattribute__(prop)
    # if prop not in LIST_TYPE_PROPS:
    #     entity_value = [entity_value]
    return _subtract_set_from_list(entity_value, parent_value)


def _get_inherited_values(parent_object, prop, inherited_values_map):
    """
    :param parent_object: PRTG instance of the parent of the object being ruled.
    :param prop: Property name.
    :param inherited_values_map: Map of cached properties.
    :return: Inherited values map (i.e., the parent_object's prop value).
    """
    if parent_object is not None and prop in INHERITED_PROPS:
        if prop in inherited_values_map:
            inherited_values = inherited_values_map[prop]
        else:
            if prop in LIST_TYPE_PROPS:
                inherited_values = set(parent_object.__getattribute__(prop))
            else:
                inherited_values = {parent_object.__getattribute__(prop)}
            inherited_values_map[prop] = inherited_values
    else:
        inherited_values = set()
        inherited_values_map[prop] = inherited_values
    return inherited_values


class Rule(object):
    """
    Application Rule.
    """

    def __init__(self, attribute, pattern, prop, update=False, value=None, remove=None, formatting=None):
        """
        """
        if update and formatting:
            raise ValueError('Cannot set "formatting" when "update" is True')
        if formatting and (value or remove):
            raise ValueError('Cannot set "value" nor "remove" if "formatting" is set')
        if not update and remove:
            raise ValueError('Cannot set "remove" when "update" is False')
        self.attribute = attribute
        self.pattern = pattern
        self.prop = prop
        self.update = update
        self.value = value if value else []
        self.remove = set(remove) if remove else set()
        self.formatting = formatting

    def eval(self, prtg_object, parent_object, inherited_values_map):
        """
        Evaluate rule on the prtg_object (it updates the object).
        :param prtg_object: PRTG instance.
        :param parent_object: The PRTG instance pointed by prtg_object.parentid.
        :param inherited_values_map: Parent values cached.
        :return: New value for the property, as string.
        """
        parent_value = _get_inherited_values(parent_object, self.prop, inherited_values_map)
        if self.formatting:
            new_value = self._format_value(prtg_object, parent_object)
        elif self.update:
            entity_value = _get_entity_value(prtg_object, self.prop, parent_value)
            new_value = self._remove_values(entity_value, self.remove)
            new_value = self._update_list_value(new_value, parent_value, self.value)
        else:
            new_value = _subtract_set_from_list(self.value, parent_value)
        if isinstance(new_value, list):
            new_value = ' '.join(new_value)
        prtg_object.update_field(self.prop, new_value, parent_value)
        return new_value

    def _format_value(self, prtg_object, parent_object):
        return self.formatting.format(entity=prtg_object, parent=parent_object)

    @staticmethod
    def _remove_values(entity_value, remove):
        return _subtract_set_from_list(entity_value, remove)

    @staticmethod
    def _update_list_value(entity_value, parent_value, value):
        current = _subtract_set_from_list(entity_value, parent_value)
        if value is None:
            value = []
        update = _subtract_set_from_list(value, parent_value.union(current))
        new_value = current + update
        return new_value

    def __repr__(self):
        return 'Rule' + str(vars(self))


class NameMatch(Rule):
    """
    Name match rule.
    """

    def matches(self, prtg_object):
        return re.match(self.pattern, str(prtg_object.__getattribute__(self.attribute)))


class RuleChain(object):
    def __init__(self, *args):
        """
        :param args: Rule dictionaries (e.g.: {attribute: 'name', ..., 'value': ['a', 'b', 'c']}, {...}).
        """
        self.rules = []
        self.append_all(*args)

    def append_all(self, *args):
        """
        Appends all rule dictionaries to the list of rules.
        :param args: Rule dictionaries (e.g.: {attribute: 'name', ..., 'value': ['a', 'b', 'c']}, {...}).
        """
        if args:
            self.rules = [NameMatch(**arg) for arg in args]

    def apply(self, prtg_object, parent_object):
        """
        Applies the rules to a PRTG object (thus modifying it).
        :param prtg_object: PRTG object to which the rule chain is applied.
        :param parent_object: Parent PRTG object.
        :return: map of changes by property, i.e., <prop, str(new_value)>.
        """
        original_object = deepcopy(prtg_object)
        changes = {}
        inherited_values_map = {}
        current_rule = None  # For exception logging
        try:
            for rule in self.rules:
                current_rule = rule
                if rule.matches(prtg_object):
                    new_value = rule.eval(prtg_object, parent_object, inherited_values_map)
                    changes[rule.prop] = new_value
            return self._get_effective_changes(original_object, inherited_values_map, changes)
        except AttributeError as exception:
            # logging.error('Unable to apply rule {} to object {}'.format(current_rule, prtg_object), exception)
            logging.error('Unable to apply rule {} to object {}'.format(current_rule, prtg_object))
            return None


    @staticmethod
    def _get_effective_changes(original_object, inherited_values_map, changes):
        """
        Crosses changes with the original values and returns only the changes that need to be applied (i.e., new values
        that match the original ones are skipped).
        :param original_object: PRTG entity.
        :param inherited_values_map: Map of parent values per property.
        :param changes: Map of all (i.e., unfiltered) changes.
        :return: Map of effective changes (i.e., changes that need to be applied), with props as keys.
        """
        effective_changes = {}
        for prop, change_value in changes.items():
            entity_value = _get_entity_value(original_object, prop, inherited_values_map[prop])
            if prop in LIST_TYPE_PROPS:
                new_value = change_value.split(' ') if change_value != '' else []
            else:
                new_value = change_value
            if set(entity_value) != set(new_value):
                effective_changes[prop] = change_value
        return effective_changes


class Query(object):
    """
    PRTG Query object. This objects will return the URL as a string and
    hold the response from the server.
    """

    __DEFAULT_MAXIMUM = 500

    targets = {
        'table': {'extension': '.xml?'}, 'getstatus': {'extension': '.xml?'}, 'getpasshash': {'extension': '.htm?'},
        'setobjectproperty': {'extension': '.htm?'}, 'getobjectproperty': {'extension': '.htm?'}
    }

    args = []
    target = ''

    url_str = '{}/api/{}username={}&password={}'
    method = 'GET'
    default_columns = ['objid', 'parentid', 'name', 'tags', 'active', 'status']

    def __init__(self, client, target, maximum=__DEFAULT_MAXIMUM, content='', objid=None, name=None, value=None,
                 parent_value=None):
        """
        :param client: prtg.client.Client instance.
        :param target: Target string (e.g.: 'table').
        :param maximum: Maximum number of items per iteration.
        :param content: If target 'table', table which is going to be queried.
        :param objid: Object Id.
        :param name: Attribute name.
        :param value: Value.
        :param parent_value: Parent object's value.
        """

        if target not in self.targets:
            raise BadTarget('Invalid API target: {}'.format(target))

        self.endpoint = client.endpoint
        self.username = client.username
        self.password = client.password
        self.method = 'GET'
        self.target = target + self.targets[target]['extension']
        self.parent_value = parent_value
        self.paginate = False
        self.response = list()
        self.counter = 0
        self.maximum = maximum
        self.extra = dict()
        self.expect_response = True

        if target == 'table':
            self.extra.update({'columns': ','.join(self.default_columns)})

        if content:
            self.extra.update({'content': content})

        if target == 'setobjectproperty':
            if not objid or not name or value is None:
                raise BadTarget
            self.extra.update({'id': objid, 'name': name, 'value': value})
            self.expect_response = False  # PRTG doesn't respond with a message, just assume 200 is ok.

        if target == 'getobjectproperty':
            if not all([objid, name]):
                raise BadTarget
            self.extra.update({'id': objid, 'name': name})

    def increment(self):
        """
        Increment counter in self.maximum, to continue iterating through the list of items.
        """
        self.counter += self.maximum

    def get_url(self):
        """
        Get query URL.
        :return: Query URL.
        """
        _url = self.url_str.format(self.endpoint, self.target, self.username, self.password)

        _url += '&start={}&count={}'.format(self.counter, self.maximum)

        if self.extra:
            _url += '&' + '&'.join(map(lambda x: '{}={}'.format(x[0], x[1]),
                                       filter(lambda z: z[1], self.extra.items())))
        return _url

    def __str__(self):
        return self.get_url()
