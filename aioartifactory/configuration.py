"""
Configuration
~~~~~~~~~~~~~
"""

###############
# Artifactory #
###############

DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT = 1_000
DEFAULT_ARTIFACTORY_SEARCH_MAX_RESULT = 500

#################
# Miscellaneous #
#################

# The maximum parallel connection use to retrieve artifact(s)
DEFAULT_MAXIMUM_CONNECTION = 1
DEFAULT_CONNECTION_TIMEOUT = 30 * 60  # 30 Minute

MAX_TIMEOUT = 3_600  # 1 hour
CHUNK_SIZE = 256 * 1_024
RETRY_COUNT = 1
RETRY_WAIT_TIME = 1.0
