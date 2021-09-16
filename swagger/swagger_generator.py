import json

import requests


def save_input():
    response = requests.get(postman_url)
    if response.status_code == 200:
        json_data = json.loads(response.text)
        json_data = json.dumps(json_data, indent=2, sort_keys=False)
        with open(input_file_name, "w") as f:
            f.write(json_data)


def save_output(generated_file_url):
    payload = {}
    headers = {"Authorization": auth_token}
    response = requests.request(
        "GET", generated_file_url, headers=headers, data=payload
    )
    print("Downloading yaml content!")
    if response.status_code == 200:
        with open(output_file_name, "wb") as f:
            f.write(response.content)
        return True
    else:
        print(response.status_code)
        return False


def generate_swagger_yaml():
    save_input()
    url = apimatic_base_url + "/api/transformations"
    payload = json.dumps(
        {"fileUrl": postman_url, "exportFormat": "Swagger20", "codeGenVersion": 1}
    )
    headers = {
        "Accept": "application/json",
        "content-type": "application/vnd.apimatic.urlTransformDto.v1+json",
        "Authorization": auth_token,
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print("Converting to yaml!")
    if response.status_code == 201:
        response_json = json.loads(response.text)
        print(response_json["id"])
        generated_file_url = apimatic_base_url + response_json["generatedFile"]
        if save_output(generated_file_url):
            print("process complete!")
    else:
        print(response.status_code)


auth_token = "Basic cnJrYTc5d2FsQGdtYWlsLmNvbTpGVnkkLjY5TjJAYk1QRFM="
apimatic_base_url = "https://www.apimatic.io"
postman_url = "https://www.getpostman.com/collections/5a84e129cd4d68226192"

input_file_name = "input_postman.json"
output_file_name = "output_swagger.yaml"

if __name__ == "__main__":
    generate_swagger_yaml()
