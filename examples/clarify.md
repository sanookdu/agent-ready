# Session storage migration (synthetic)

Replace authentication session storage with the approved new persistence service.
The service and implementation environment are available, and the team is authorized
to migrate. The owner has not decided whether active sessions must remain valid
through cutover or all users may be logged out. These alternatives change migration
behavior and acceptance tests. The existing session serializer and storage adapter
can be located by inspecting the code during implementation.
