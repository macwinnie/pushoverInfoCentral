# InfoCentral

## Database Migrations

For being able to develop the database, this repo works with `yoyo-migrations` for migrations.

New DB migrations can be created by running `yoyo new ./db_migrations -m "description of migration"` from the `src` directory (or working directory after starting Docker container by `docker-compose up -d`).  
*Attention*: `pip` requirements from `requirements.txt` have to be installed!

## Watchers

Within the directory `src/watcher`, one can define python files as watchers. They need to have a `watch` function, that accepts the two parameters `database` and `pushover`. This function defines, what will be performed as watch action on the specific watcher.

The two watchers `git` and `pushover` are the first ones defined:

* the `pushover` watcher simply fetches receipts of prio 2 Pushover messages
* the `git` watcher allows one to watch (public) Git repositories for new commits or tags
    * The environmental variable `WATCH_GIT_REPOS` defines the list (`[]`) repos to be watched.
    * Each element of this list is a dictionary with two key-value-pairs:
        * `repo_url` defines the Git URL (string)
        * `watch` defines the actual watch command (dictionary `{}`)
            * `watch` may be `tags` or `commits`
            * `priority` defines the priority to be used for Pushover message (defaults to `0`) (see [Pushover Documentation](https://pushover.net/api))
            * `title` defines the Pushover title of message (defaults to `EMPTY`)
            * `message` defines the Pushover message (default message for `tag` and `commit`)
            * `url` defines the Pushover url of message (defaults to `EMPTY`)
            * `url_title` defines the Pushover title for url of message (defaults to `EMPTY`)
            * each of the keys (but `watch` and `priority`) can use those placeholders:
                * `{tag}` current tag (`watch`: `tags`)
                * `{commit}` current commit identifier shortened to 8 chars (`watch`: `commits`)
                * `{commit_id}` current commit identifier (`watch`: `commits`)
                * `{commit_message}` message published with current commit (`watch`: `commits`)
