# -*- coding: utf-8 -*-

from copy import deepcopy
import logging
import re

from prtg.models import INHERITED_PROPS, LIST_TYPE_PROPS


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
    if isinstance(entity_value, str):
        entity_value = [entity_value]
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

    def __init__(self, attribute, pattern, prop, update=False, value=None, remove=None, formatting=None,
                 rollback_formatting=None):
        """
        """
        if formatting and (value or remove):
            raise ValueError('Cannot set "value" nor "remove" if "formatting" is set')
        if rollback_formatting and remove:
            raise ValueError('Cannot set "remove" if "rollback_formatting" is set')
        if not update and remove:
            raise ValueError('Cannot set "remove" when "update" is False')
        if rollback_formatting is not None and '{entity.' + prop + '}' not in rollback_formatting:
            raise ValueError("Cannot have \"rollback_formatting\" without references to the entity's property in pure "
                             "form")
        self.attribute = attribute
        self.pattern = pattern
        self.prop = prop
        self.update = update
        self.value = value if value else []
        self.remove = set(remove) if remove else set()
        self.formatting = formatting
        self.rollback_formatting = rollback_formatting

    def eval(self, prtg_object, parent_object, inherited_values_map):
        """
        Evaluate rule on the prtg_object (it updates the object).
        :param prtg_object: PRTG instance.
        :param parent_object: The PRTG instance pointed by prtg_object.parentid.
        :param inherited_values_map: Parent values cached.
        :return: New value for the property, as string.
        """
        parent_value = _get_inherited_values(parent_object, self.prop, inherited_values_map)
        if self.rollback_formatting:
            new_value = self._rollback_applied_formatting(prtg_object, parent_object, inherited_values_map)
            self._update_field(prtg_object, self.prop, new_value, parent_value)
        if self.formatting:
            new_value = self._apply_formatting(prtg_object, parent_object, inherited_values_map)
        elif self.update:
            entity_value = _get_entity_value(prtg_object, self.prop, parent_value)
            new_value = self._remove_values(entity_value, self.remove)
            new_value = self._update_list_value(new_value, parent_value, self.value)
        elif not self.rollback_formatting:
            new_value = _subtract_set_from_list(self.value, parent_value)
        return self._update_field(prtg_object, self.prop, new_value, parent_value)

    def _apply_formatting(self, prtg_object, parent_object, inherited_values_map):
        value = ' '.join(_get_entity_value(prtg_object, self.prop,
                                           _get_inherited_values(parent_object, self.prop, inherited_values_map)))
        regexp = ('^' +
                  '(.*)'.join([re.escape(self._format_value(x, prtg_object, parent_object))
                               for x in self.formatting.split('{entity.' + self.prop + '}')]) +
                  '$')
        match = re.compile(regexp).match(value)
        if not match:
            new_object = prtg_object
            if self.update:
                regexp = ('^' +

                          '(.*)'.join(['(?:.*)'.join([re.escape(self._format_value(x, prtg_object, parent_object))
                                                      for x in re.split('\{parent\.[^\}]+\}', part)])
                                       for part in self.formatting.split('{entity.' + self.prop + '}')]) +
                          '$')
                match = re.compile(regexp).match(value)
                if match:
                    groups = match.groups()  # This has at least one member
                    consistent = True
                    for group in groups:
                        if groups[0] != group:
                            logging.error('There are inconsistencies in the original value of the property in '
                                          'entity {}.'.format(prtg_object.name))
                            consistent = False
                            break
                    if not consistent:
                        raise AttributeError()
                    new_object = deepcopy(prtg_object)
                    setattr(new_object, self.prop, match.groups()[0])
            value = self._format_value(self.formatting, new_object, parent_object)
        return value

    def _rollback_applied_formatting(self, prtg_object, parent_object, inherited_values_map):
        value = ' '.join(_get_entity_value(prtg_object, self.prop,
                                           _get_inherited_values(parent_object, self.prop, inherited_values_map)))
        regexp = ('^' +
                  '(.*)'.join([re.escape(self._format_value(x, prtg_object, parent_object))
                               for x in self.rollback_formatting.split('{entity.' + self.prop + '}')]) +
                  '$')
        match = re.compile(regexp).match(value)
        if not match:
            raise AttributeError()
        groups = match.groups()  # This has at least one member
        consistent = True
        for group in groups:
            if groups[0] != group:
                logging.error('There are inconsistencies in the original value of the property in entity {}.'.format(
                    prtg_object.name))
                consistent = False
                break
        if not consistent:
            raise AttributeError()
        return groups[0]

    @staticmethod
    def _format_value(formatting, prtg_object, parent_object):
        return formatting.format(entity=prtg_object, parent=parent_object)

    @staticmethod
    def _remove_values(entity_value, remove):
        return _subtract_set_from_list(entity_value, remove)

    @staticmethod
    def _update_field(prtg_object, prop, new_value, parent_value):
        if isinstance(new_value, list):
            new_value = ' '.join(new_value)
        prtg_object.update_field(prop, new_value, parent_value)
        return new_value

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
        except AttributeError:
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
                new_value = [change_value]
            if set(entity_value) != set(new_value):
                effective_changes[prop] = change_value
        return effective_changes
