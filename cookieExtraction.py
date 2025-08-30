import json

with open('cookies.json') as f:
    cookies = json.load(f)
cookie_value = cookies.get('sessionid')  # Replace with your cookie name

headers = {
    'Cookie': f'sessionid={cookie_value}'
}
response = requests.get(url, headers=headers)


#
#To dynamically pick up a cookie value from a browser session, you generally need to:

#E#xport the cookie from your browser (using browser extensions or developer tools).
#Read the cookie value in your Python code (from a file or clipboard).
#Pass the cookie in your REST request headers.
#Example workflow:

#Use a browser extension like "EditThisCookie" (Chrome) to export cookies as JSON.
#Save the cookie value to a file (e.g., cookies.json).
#In your Python code, read the cookie and add it to the headers:
