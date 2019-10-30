import os

from keystoneauth1 import session
from keystoneauth1.identity import v3
from swiftclient import client as sw_client, exceptions as sw_exceptions


def _get_authenticated_client():
    """
    @rtype: swiftclient.client.Connection
    @returns: an token authenticated Swift client.
    """
    auth = v3.Token(auth_url=os.environ['OS_AUTH_URL'],
                    token=os.environ['OS_AUTH_TOKEN'],
                    project_name=os.environ['OS_PROJECT_NAME'],
                    project_domain_id=os.environ['OS_PROJECT_DOMAIN_ID'])

    sess = session.Session(auth=auth)
    return sw_client.Connection(session=sess)


def create_public_container(container_name):
    """
    Create a new container marked as public. If it exists, the existing
    container will be set as public.

    @type container_name: str
    @param container_name: the container name
    """
    client = _get_authenticated_client()

    # svc = sw_service.SwiftService()  # options=swift_options)
    # return svc.post(container_name, options={"read_acl": '.r:*'})

    try:
        client.head_container(container_name) # check if container exists
        client.post_container(container_name, {'X-Container-Read': '.r:*'})
    except sw_exceptions.ClientException:
        client.put_container(container_name, {'X-Container-Read': '.r:*'})


def put_object(container_name, key, value):
    """
    Post a key into a public container. If container not exists,
    this function will create one. If it exists, the conainer will be
    turned a public one.

    @returns: object URL
    """
    client = _get_authenticated_client()

    # svc = sw_service.SwiftService()  # options=swift_options)
    # return svc.post(container_name, options={"read_acl": '.r:*'})

    client.put_object(container_name, key, value)

    return "{:}/{:}/{:}".format(client.url, container_name, key)


def delete_container(container_name):
    client = _get_authenticated_client()

    # svc = sw_service.SwiftService()  # options=swift_options)
    # return svc.post(container_name, options={"read_acl": '.r:*'})

    client.delete_container(container_name)


if __name__ == "__main__":
    print("[INFO] Creating a new container named 'TestContainer'...")
    create_public_container("TestContainer")
    print("[INFO] Done!")

    print("[INFO] Adding a new object \"TestKey\": \"TestValue\"...")
    print(put_object("TestContainer", "TestKey", "TestValue"))
    print("[INFO] Done!")
