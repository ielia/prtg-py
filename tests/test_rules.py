import unittest

from prtg.models import Device, NameMatch, RuleChain


DEVICE_COMMON_ARGS = {'objid': 123, 'name': 'aba'}


def build_common_device(tags, name='a device'):
    device_args = DEVICE_COMMON_ARGS.copy()
    device_args['tags'] = tags
    device_args['name'] = name
    return Device(**device_args)


def build_tags_rule_dict(update, value=None, remove=None, pattern='^a'):
    rule = {'attribute': 'name', 'pattern': pattern, 'prop': 'tags', 'update': update}
    if value is not None:
        rule['value'] = value
    if remove is not None:
        rule['remove'] = remove
    return rule


class TestRule(unittest.TestCase):
    def test_get_new_value_adds_no_duplicates(self):
        # 'ta' is duplicated by "value",
        # 'tb' stays untouched,
        # 'tc' is inherited from the parent (so it is not present in the new value),
        # 'td' is added by "value".
        rule = NameMatch(**build_tags_rule_dict(True, ['ta', 'td']))
        parent_value = {'tc'}
        new_value = rule.eval(['ta', 'tb', 'tc'], parent_value)
        self.assertEqual({'ta', 'tb', 'td'}, set(new_value))

    def test_get_new_value_removes_original_entity_values_only(self):
        # 'ta' and 'tc' are inherited from the parent (so they are not present in the new value),
        # 'tb' is removed by "remove" and re-added by "value",
        # 'td' is removed by the "remove" in the rule,
        # 'te' stays untouched,
        # 'tf' is not removed by "remove" (because it is not in the original) and added by "value",
        # 'tg' is added by "value".
        rule = NameMatch(**build_tags_rule_dict(True, ['ta', 'tb', 'tf', 'tg'], ['tb', 'tc', 'td', 'tf']))
        parent_value = {'ta', 'tc'}
        new_value = rule.eval(['ta', 'tb', 'tc', 'td', 'te'], parent_value)
        self.assertEqual({'tb', 'te', 'tf', 'tg'}, set(new_value))

    def test_not_update(self):
        # 'ta' is inherited from the parent (so it is not present in the new value);
        # 'tb' is not removed by "remove" because it is not overwritten by "value";
        # 'tc' is not removed by "remove", but it is not overwritten by "value" either;
        # 'td' is not overwritten by "value";
        # 'te' is in overwritten by "value".
        rule = NameMatch(**build_tags_rule_dict(False, ['ta', 'tb', 'te'], ['ta', 'tb', 'tc']))
        parent_value = {'ta'}
        new_value = rule.eval(['ta', 'tb', 'tc', 'td'], parent_value)
        self.assertEqual({'tb', 'te'}, set(new_value))

    # def test_keep(self):
    #     # 'ta' and 'tc' are inherited from the parent (so they are not present in the new value),
    #     # 'tb' is not removed by "remove" because of "keep" and then a duplicate in "value",
    #     # 'td' is not removed by "remove" because of "keep",
    #     # 'te' stays untouched (and kept by "keep"),
    #     # 'tf' is removed by "remove" and re-added by "value",
    #     # 'tg' os added by "value",
    #     # 'th' is not kept by "keep" because it was not added by "value" nor present in the original.
    #     rule = NameMatch(**build_common_rule_dict(True, ['ta', 'tb', 'tf', 'tg'], ['tb', 'tc', 'td', 'tf'],
    #                                               ['ta', 'tb', 'tc', 'td', 'te', 'th']))
    #     parent_value = {'ta', 'tc'}
    #     new_value = rule.eval(['ta', 'tb', 'tc', 'td', 'te'], parent_value)
    #     self.assertEqual({'tb', 'td', 'te', 'tf', 'tg'}, set(new_value))


class TestRuleChain(unittest.TestCase):
    def test_tags_chain(self):
        # 'ta' is inherited from the parent (so it is not present in the new value);
        # 'tb' is not removed by "remove" because it is not overwritten by "value";
        # 'tc' is not removed by "remove", but it is not overwritten by "value" either;
        # 'td' is not overwritten by "value";
        # 'te' is in overwritten by "value".
        device = build_common_device(['ta', 'tb', 'tc', 'td'])
        rule_dict1 = build_tags_rule_dict(True, ['ta', 'te'], ['ta', 'tc'])
        rule_dict2 = build_tags_rule_dict(True, ['tf'], ['td', 'tg'])
        rule_dict3 = build_tags_rule_dict(True, ['th'])
        rule_dict4 = build_tags_rule_dict(True, None, ['tf'])
        rule_chain = RuleChain(rule_dict1, rule_dict2, rule_dict3, rule_dict4)
        parent = build_common_device({'ta', 'tb'})
        changes = rule_chain.apply(device, parent)
        self._assert_device_tags_and_changes({'te', 'th'}, True, device, parent, changes)

    def test_no_match(self):
        device = build_common_device(['ta', 'tb', 'tc', 'td'], 'some other device')
        rule_dict = build_tags_rule_dict(True, ['ta', 'te'], ['ta', 'tc'])
        rule_chain = RuleChain(rule_dict)
        parent = build_common_device({'ta', 'tb'})
        changes = rule_chain.apply(device, parent)
        self._assert_device_tags_and_changes({'tc', 'td'}, False, device, parent, changes)

    def test_no_changes(self):
        device = build_common_device(['ta', 'tb', 'tc'])
        rule_dict1 = build_tags_rule_dict(True, ['ta', 'tb'], ['ta', 'tc'])
        rule_dict2 = build_tags_rule_dict(True, ['tc'], ['td'])
        rule_chain = RuleChain(rule_dict1, rule_dict2)
        parent = build_common_device({'ta'})
        changes = rule_chain.apply(device, parent)
        self._assert_device_tags_and_changes({'tb', 'tc'}, False, device, parent, changes)

    def test_no_changes_when_cleaning_all(self):
        device = build_common_device(['ta'])
        rule_dict = build_tags_rule_dict(False, [])
        rule_chain = RuleChain(rule_dict)
        parent = build_common_device({'ta'})
        changes = rule_chain.apply(device, parent)
        self._assert_device_tags_and_changes(set(), False, device, parent, changes)

    def test_tags_chain_no_update_in_the_middle(self):
        # 'ta' is inherited from the parent (so it is not present in the new value);
        # 'tb', 'tc' and 'td are removed by no-update "value";
        # 'te' is added by no-update "value";
        # 'tf' is added by no-update "value" and then removed by "remove";
        # 'tg' is added by "value".
        device = build_common_device(['ta', 'tb', 'tc'])
        rule_dict1 = build_tags_rule_dict(True, ['ta', 'td'], ['ta', 'tc'])
        rule_dict2 = build_tags_rule_dict(False, ['te', 'tf'])
        rule_dict3 = build_tags_rule_dict(True, ['tg'], ['tf'])
        rule_chain = RuleChain(rule_dict1, rule_dict2, rule_dict3)
        parent = build_common_device({'ta'})
        changes = rule_chain.apply(device, parent)
        self._assert_device_tags_and_changes({'te', 'tg'}, True, device, parent, changes)

    def _assert_device_tags_and_changes(self, expected_new_value_dict, changed, device, parent, changes):
        self.assertEqual(list, type(device.tags))
        self.assertEqual(expected_new_value_dict.union(parent.tags), set(device.tags))
        if changed:
            self.assertEqual({'tags'}, changes.keys())
            changed_tags = changes['tags']
            self.assertEqual(str, type(changed_tags))
            self.assertEqual(expected_new_value_dict, set(changed_tags.split(' ')))
        else:
            self.assertEqual(set(), changes.keys())
