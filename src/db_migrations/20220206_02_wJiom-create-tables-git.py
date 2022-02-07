"""
CREATE TABLEs git
"""

from yoyo import step

__depends__ = {'20220206_01_zLEIt-create-table-messages'}

steps = [
    step( """
        CREATE TABLE git_repos (
            id      INTEGER       NOT NULL PRIMARY KEY AUTOINCREMENT,
            url     VARCHAR(2048)          DEFAULT NULL,
            created DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """ ),
    step( """
        CREATE TABLE git_commits (
            id         INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
            repo_id    INTEGER     NOT NULL,
            ident      VARCHAR(40) NOT NULL,
            message    TEXT        NOT NULL,
            registered DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """ ),
    step( """
        CREATE TABLE git_tags (
            id         INTEGER      NOT NULL PRIMARY KEY AUTOINCREMENT,
            repo_id    INTEGER      NOT NULL,
            name       VARCHAR(512) NOT NULL,
            registered DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """ )
]
