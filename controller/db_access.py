import sqlite3
import _conf as conf

"""
DB_ACCESS

A layer providing functions for interacting with the database.
"""

# DB
conn = sqlite3.connect(conf.DATABASE_PATH)
conn.execute('PRAGMA foreign_keys = 1')
conn.row_factory = sqlite3.Row  # Allows for accessing query results like a dictionary which is more readable
cursor = conn.cursor()


def create_policy(policy_uri):
    """
    Creates a new Policy with the given URI
    """
    if policy_exists(policy_uri):
        raise ValueError('A Policy with that URI already exists.')
    cursor.execute('INSERT INTO POLICY (URI, CREATED) VALUES ("{uri}", CURRENT_TIMESTAMP);'.format(uri=policy_uri))
    conn.commit()


def delete_policy(policy_uri):
    """
    Deletes the Policy with the given URI
    """
    conn.execute('DELETE FROM POLICY WHERE URI = "{uri:s}"'.format(uri=policy_uri))
    conn.commit()


def policy_exists(policy_uri):
    """
    Checks whether a Policy with the given URI exists

    :return:    True if the policy exists
                False if the policy does not exist
    """
    cursor.execute('SELECT COUNT(1) FROM POLICY WHERE URI = "{uri:s}"'.format(uri=policy_uri))
    return cursor.fetchone()[0]


def set_policy_attribute(policy_uri, attr, value):
    """
    For a given Policy, set an attribute to the given value

    :param policy_uri:
    :param attr: Permitted attributes - TYPE, LABEL, JURISDICTION, LEGAL_CODE, HAS_VERSION, LANGUAGE, SEE_ALSO, SAME_AS,
                                        COMMENT, LOGO, STATUS
    :param value:
    """
    permitted_attributes = ['TYPE', 'LABEL', 'JURISDICTION', 'LEGAL_CODE', 'HAS_VERSION', 'LANGUAGE', 'SEE_ALSO',
                            'SAME_AS', 'COMMENT', 'LOGO', 'STATUS']
    attr = attr.upper()
    if attr not in permitted_attributes:
        raise ValueError('Attribute \'' + attr + '\' is not permitted.')
    if not policy_exists(policy_uri):
        raise ValueError('Policy with URI ' + policy_uri + ' does not exist.')
    conn.execute(
        'UPDATE POLICY SET {attr:s} = "{value:s}" WHERE URI = "{uri:s}";'.format(attr=attr, value=value, uri=policy_uri)
    )
    conn.commit()


def get_policy(policy_uri):
    """
    Retrieve all the relevant information about a Policy, including its attributes and its Rules. Additionally, the
    Actions, Assignors and Assignees for each of those rules.

    :return: A Dictionary containing the following elements:
                URI - string
                TYPE - string
                LABEL - string
                JURISDICTION - string
                LEGAL_CODE - string
                HAS_VERSION - string
                LANGUAGE - string
                SEE_ALSO - string
                SAME_AS - string
                COMMENT - string
                LOGO - string
                CREATED - string
                STATUS - string
                RULES - List of Rules
                    Each Rule is a Dictionary containing the following elements:
                        URI - string
                        TYPE - string
                        LABEL - string
                        ASSIGNORS - List of strings
                        ASSIGNEES - List of strings
                        ACTIONS - List of Actions
                            Each Action is a Dictionary containing the following elements:
                            URI - string
                            LABEL - string
                            DEFINITION - string
    """
    cursor.execute('SELECT * FROM POLICY WHERE URI = "{uri}"'.format(uri=policy_uri))
    policy_result = cursor.fetchone()
    if policy_result is None:
        raise ValueError('Policy with URI ' + policy_uri + ' does not exist.')
    policy = dict(policy_result)
    policy['RULES'] = get_rules_for_policy(policy_uri)
    return policy


def get_all_policies():
    """
    Returns a lists of all Policy URIs
    """
    cursor.execute('SELECT URI FROM POLICY')
    policies = list()
    for result in cursor.fetchall():
        policies.append(result['URI'])
    return policies


def policy_has_rule(policy_uri, rule_uri):
    """
    Checks if the given Policy includes the given Rule
    """
    query_str = 'SELECT COUNT(1) FROM POLICY_HAS_RULE WHERE POLICY_URI = "{policy_uri}" AND RULE_URI = "{rule_uri}"'
    cursor.execute(query_str.format(policy_uri=policy_uri, rule_uri=rule_uri))
    return cursor.fetchone()[0]


def add_asset(asset_uri, policy_uri):
    """
    Assigns an existing Asset to an existing Policy.
    """
    if not policy_exists(policy_uri):
        raise ValueError('Policy with URI ' + asset_uri + ' does not exist.')
    if asset_exists(asset_uri):
        raise ValueError('An Asset with that URI already exists.')
    query_str = 'INSERT INTO ASSET (URI, POLICY_URI) VALUES ("{uri}", "{policy_uri}")'
    cursor.execute(query_str.format(uri=asset_uri, policy_uri=policy_uri))
    conn.commit()


def remove_asset(asset_uri):
    """
    Removes an Asset from its Policy
    """
    conn.execute('DELETE FROM ASSET WHERE URI = "{uri:s}"'.format(uri=asset_uri))
    conn.commit()


def asset_exists(uri):
    """
    Checks whether an Asset with a given URI has a record in the database

    :return:    True if the asset exists
                False if the asset does not exist
    """
    cursor.execute('SELECT COUNT(1) FROM ASSET WHERE URI = "{uri:s}"'.format(uri=uri))
    return cursor.fetchone()[0]


def get_all_assets():
    """
    Returns a list of all Asset URIs
    """
    cursor.execute('SELECT URI FROM ASSET')
    results = cursor.fetchall()
    assets = list()
    for asset in results:
        assets.append(asset['URI'])
    return assets


def create_rule(rule_uri, rule_type, rule_label):
    """
    Creates a new Rule with the given URI and rule type.

    :param rule_uri:
    :param rule_type: Permitted rule types: http://www.w3.org/ns/odrl/2/permission
                                            http://www.w3.org/ns/odrl/2/prohibition
                                            http://www.w3.org/ns/odrl/2/duty
    :param rule_label:
    """
    if rule_exists(rule_uri):
        raise ValueError('A Rule with that URI already exists.')
    if rule_type not in get_permitted_rule_types():
        raise ValueError('Rule type ' + rule_type + ' is not permitted.')
    if not rule_label:
        raise ValueError('Rule must have a label.')
    query_str = 'INSERT INTO RULE (URI, TYPE, LABEL) VALUES ("{uri}", "{rule_type}", "{label}")'
    cursor.execute(query_str.format(uri=rule_uri, rule_type=rule_type, label=rule_label))
    conn.commit()


def delete_rule(rule_uri):
    """
    Deletes the Rule with the given URI. A Rule can only be deleted if it is not currently assigned to a policy.
    """
    if len(get_policies_for_rule(rule_uri)) > 0:
        raise ValueError('Cannot delete a Rule while it is assigned to a Policy.')
    conn.execute('DELETE FROM RULE WHERE URI = "{uri}"'.format(uri=rule_uri))
    conn.commit()


def add_rule_to_policy(rule_uri, policy_uri):
    """
    Assigns a Rule to a policy. Policies are made up of many Rules. Rules can be reused in multiple Policies.
    """
    if not rule_exists(rule_uri):
        raise ValueError('Rule with URI ' + rule_uri + ' does not exist.')
    if not policy_exists(policy_uri):
        raise ValueError('Policy with URI ' + policy_uri + ' does not exist.')
    if policy_has_rule(policy_uri, rule_uri):
        raise ValueError('Rule ' + rule_uri + ' is already included in Policy ' + policy_uri + '.')
    query_str = 'INSERT INTO POLICY_HAS_RULE (POLICY_URI, RULE_URI) VALUES ("{policy_uri}", "{rule_uri}")'
    conn.execute(query_str.format(policy_uri=policy_uri, rule_uri=rule_uri))


def remove_rule_from_policy(rule_uri, policy_uri):
    """
    Removes a Rule from a Policy. The Rule will still exist unless deleted, but is not assigned to that Policy anymore.
    """
    conn.execute('''
        DELETE FROM POLICY_HAS_RULE
        WHERE RULE_URI = "{rule_uri}" AND POLICY_URI IN (
            SELECT URI FROM POLICY WHERE URI = "{policy_uri}"
        )'''.format(rule_uri=rule_uri, policy_uri=policy_uri))


def get_rules_for_policy(policy_uri):
    """
    Retrieves all the Rules used by a Policy with the given URI.

    :return: A List of Rules
                Each Rule is a Dictionary containing the following elements:
                    URI - string
                    TYPE - string
                    LABEL - string
                    ASSIGNORS - List of strings
                    ASSIGNEES - List of strings
                    ACTIONS - List of Actions
                        Each Action is a Dictionary containing the following elements:
                        URI - string
                        LABEL - string
                        DEFINITION - string
    """
    query_str = '''
        SELECT R.URI, R.TYPE, R.LABEL FROM RULE R, POLICY_HAS_RULE P_R, POLICY P
        WHERE R.URI = P_R.RULE_URI AND P_R.POLICY_URI = P.URI AND P.URI = "{policy_uri}"
    '''
    cursor.execute(query_str.format(policy_uri=policy_uri))
    rules_results = cursor.fetchall()
    rules = list()
    for rule_result in rules_results:
        rule = dict(rule_result)
        rule['ACTIONS'] = get_actions_for_rule(rule['URI'])
        rule['ASSIGNORS'] = get_assignors_for_rule(rule['URI'])
        rule['ASSIGNEES'] = get_assignees_for_rule(rule['URI'])
        rules.append(rule)
    return rules


def get_all_rules():
    """
    Returns a list with all Rule URIs
    """
    cursor.execute('SELECT URI FROM RULE')
    results = cursor.fetchall()
    rules = list()
    for asset in results:
        rules.append(asset['URI'])
    return rules


def rule_exists(rule_uri):
    """
    Checks if a Rule with the given URI exists

    :return:    True if the Rule exists
                False if the Rule does not exist
    """
    cursor.execute('SELECT COUNT(1) FROM RULE WHERE URI = "{uri}"'.format(uri=rule_uri))
    return cursor.fetchone()[0]


def get_permitted_rule_types():
    """
    Returns a list of all the rules types which are permitted

    Should be: http://www.w3.org/ns/odrl/2/permission
               http://www.w3.org/ns/odrl/2/prohibition
               http://www.w3.org/ns/odrl/2/duty
    However, they can be add/removed from the database at will so using this method to check is advised
    """
    cursor.execute('SELECT TYPE FROM RULE_TYPE')
    permitted_rule_types = list()
    for rule_type in cursor.fetchall():
        permitted_rule_types.append(rule_type['TYPE'])
    return permitted_rule_types


def get_policies_for_rule(rule_uri):
    """
    Returns a list of all the Policies which use the Rule given
    """
    cursor.execute('SELECT POLICY_URI FROM POLICY_HAS_RULE WHERE RULE_URI = "{rule_uri}"'.format(rule_uri=rule_uri))
    results = cursor.fetchall()
    policies = list()
    for result in results:
        policies.append(result['POLICY_URI'])
    return policies


def action_exists(action_uri):
    """
    Checks if an Action with the given URI exists

    :return:    True if the Action exists
                False if the Action does not exist
    """
    cursor.execute('SELECT COUNT(1) FROM ACTION WHERE URI = "{uri}"'.format(uri=action_uri))
    return cursor.fetchone()[0]


def add_action_to_rule(action_uri, rule_uri):
    """
    Assign an Action to a Rule. Rules can have multiple Actions associated with them, and Actions can be associated with
    multiple Rules
    """
    if not rule_exists(rule_uri):
        raise ValueError('Rule with URI ' + str(rule_uri) + ' does not exist.')
    if not action_exists(action_uri):
        raise ValueError('Action with URI ' + action_uri + ' is not permitted.')
    if rule_has_action(rule_uri, action_uri):
        raise ValueError('Rule ' + rule_uri + ' already includes Action ' + action_uri + '.')
    query_str = 'INSERT INTO RULE_HAS_ACTION (RULE_URI, ACTION_URI) VALUES ("{rule_uri}", "{action_uri}")'
    conn.execute(query_str.format(rule_uri=rule_uri, action_uri=action_uri))
    conn.commit()


def remove_action_from_rule(action_uri, rule_uri):
    """
    Removes an Action from a Rule.
    """
    query_str = 'DELETE FROM RULE_HAS_ACTION WHERE RULE_URI = "{rule_uri}" AND ACTION_URI = "{action_uri}"'
    conn.execute(query_str.format(rule_uri=rule_uri, action_uri=action_uri))
    conn.commit()


def get_actions_for_rule(rule_uri):
    """
    Returns a list of all the Actions which are assigned to a given Rule
    """
    cursor.execute('''
        SELECT A.URI, A.LABEL, A.DEFINITION FROM ACTION A, RULE_HAS_ACTION R_A 
        WHERE R_A.RULE_URI = "{rule_uri}"
        AND R_A.ACTION_URI = A.URI
    '''.format(rule_uri=rule_uri))
    results = cursor.fetchall()
    actions = list()
    for result in results:
        actions.append(dict(result))
    return actions


def rule_has_action(rule_uri, action_uri):
    """
    Checks if a Rule has an Action
    """
    query_str = 'SELECT COUNT(1) FROM RULE_HAS_ACTION WHERE RULE_URI = "{rule_uri}" AND ACTION_URI = "{action_uri}"'
    cursor.execute(query_str.format(rule_uri=rule_uri, action_uri=action_uri))
    return cursor.fetchone()[0]


def get_all_actions():
    """
    Returns a list of all the Actions which are permitted along with their label and definition

    :return A list of Actions
                Each Action is a dictionary with elements: URI, LABEL, DEFINITION
    """
    cursor.execute('SELECT URI, LABEL, DEFINITION FROM ACTION')
    results = cursor.fetchall()
    actions = list()
    for result in results:
        actions.append({'URI': result['URI'], 'LABEL': result['LABEL'], 'DEFINITION': result['DEFINITION']})
    return actions


def add_assignor_to_rule(assignor_uri, rule_uri):
    """
    Add an Assignor to a Rule
    """
    if not rule_exists(rule_uri):
        raise ValueError('Rule with URI ' + rule_uri + ' does not exist.')
    if rule_has_assignor(rule_uri, assignor_uri):
        raise ValueError('Rule ' + rule_uri + ' already has an Assignor with URI ' + assignor_uri + '.')
    query_str = 'INSERT INTO ASSIGNOR (ASSIGNOR_URI, RULE_URI) VALUES ("{assignor_uri}", "{rule_uri}")'
    conn.execute(query_str.format(assignor_uri=assignor_uri, rule_uri=rule_uri))
    conn.commit()


def remove_assignor_from_rule(assignor_uri, rule_uri):
    """
    Remove an Assignor from a Rule
    """
    query_str = 'DELETE FROM ASSIGNOR WHERE RULE_URI = "{rule_uri}" AND ASSIGNOR_URI = "{assignor_uri}"'
    conn.execute(query_str.format(assignor_uri=assignor_uri, rule_uri=rule_uri))
    conn.commit()


def rule_has_assignor(rule_uri, assignor_uri):
    """
    Checks if a Rule has an Assignor with the given URI

    :return:    True if the Rule has the Assignor
                False if the Rule does not have the Assignor
    """
    query_str = 'SELECT COUNT(1) FROM ASSIGNOR WHERE RULE_URI = "{rule_uri}" AND ASSIGNOR_URI = "{assignor_uri}"'
    cursor.execute(query_str.format(rule_uri=rule_uri, assignor_uri=assignor_uri))
    return cursor.fetchone()[0]


def get_assignors_for_rule(rule_uri):
    """
    Returns a list of URIs for all Assignors associated with a given Rule
    """
    cursor.execute('SELECT ASSIGNOR_URI FROM ASSIGNOR WHERE RULE_URI = "{rule_uri}"'.format(rule_uri=rule_uri))
    assignors = list()
    for result in cursor.fetchall():
        assignors.append(result['ASSIGNOR_URI'])
    return assignors


def add_assignee_to_rule(assignee_uri, rule_uri):
    """
    Add an Assignee to a Rule
    """
    if not rule_exists(rule_uri):
        raise ValueError('Rule with URI ' + rule_uri + ' does not exist.')
    if rule_has_assignee(rule_uri, assignee_uri):
        raise ValueError('Rule ' + rule_uri + ' already has an Assignee with URI ' + assignee_uri + '.')
    query_str = 'INSERT INTO ASSIGNEE (ASSIGNEE_URI, RULE_URI) VALUES ("{assignee_uri}", "{rule_uri}")'
    conn.execute(query_str.format(assignee_uri=assignee_uri, rule_uri=rule_uri))
    conn.commit()


def remove_assignee_from_rule(assignee_uri, rule_uri):
    """
    Remove an Assignee from a Rule
    """
    query_str = 'DELETE FROM ASSIGNEE WHERE RULE_URI = "{rule_uri}" AND ASSIGNEE_URI = "{assignee_uri}"'
    conn.execute(query_str.format(assignee_uri=assignee_uri, rule_uri=rule_uri))
    conn.commit()


def rule_has_assignee(rule_uri, assignee_uri):
    """
    Checks if a Rule has an Assignee with the given URI

    :return:    True if the Rule has the Assignee
                False if the Rule does not have the Assignee
    """
    query_str = 'SELECT COUNT(1) FROM ASSIGNEE WHERE RULE_URI = "{rule_uri}" AND ASSIGNEE_URI = "{assignee_uri}"'
    cursor.execute(query_str.format(rule_uri=rule_uri, assignee_uri=assignee_uri))
    return cursor.fetchone()[0]


def get_assignees_for_rule(rule_uri):
    """
    Returns a list of URIs for all Assignees associated with a given Rule
    """
    cursor.execute('SELECT ASSIGNEE_URI FROM ASSIGNEE WHERE RULE_URI = "{rule_uri}"'.format(rule_uri=rule_uri))
    assignees = list()
    for result in cursor.fetchall():
        assignees.append(result['ASSIGNEE_URI'])
    return assignees


def query(query_str):
    """
    Submit a custom query to the database
    """
    cursor.execute(query_str)
    return cursor.fetchall()
