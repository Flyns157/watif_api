db.createUser({
    user: "admin",
    pwd: "password",
    roles: [{ role: "userAdminAnyDatabase", db: "admin" }]
});

db.createUser({
    user: "myUser",
    pwd: "myPassword",
    roles: [{ role: "readWrite", db: "mydatabase" }]
});
