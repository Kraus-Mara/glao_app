Docs : 
- https://docs.frappe.io/framework/user/en/installation
- https://docs.frappe.io/framework/user/en/tutorial/install-and-setup-bench
- https://docs.frappe.io/framework/user/en/tutorial/create-a-site
### How to re-install everything

Start by installing all the dependencies,
then 
```bash
bench init [my-bench] --frappe-branch version-16 --python python3.14
cd [my-bench]
```

Now you need to create a site to host the GLAO app on, so type 
```bash
bench new-site [my-site]
```

Now that the site exists, you must do 2 things : set it as default site, and install the glao_app
```bash
bench use [my-site]
bench get-app https://github.com/Kraus-Mara/glao_app --branch develop # This downloads the app
bench install-app glao_app
```
Did everything went well ? Check it with 
```bash
bench --site [my-site] list-apps
```
This command should return 
```
frappe
glao_app
```
Now just do the usual
```bash
bench start
```
and go to 
http://localhost:[port] (which can be found inside the terminal where bench start was launched)

Now you can connect with the credentials that u typed when creating the site.
If the site stutters/(is) laggy : 
another tab in the azure shell, type :
```bash
bench clear-cache
bench clear-website-cache
bench build
bench export-fixtures
bench restart
```

