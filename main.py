import os
import requests
import random

from urllib.parse import urlparse, unquote
from dotenv import load_dotenv


# def get_extension(url):
#     _, extension = splitext(urlparse(url).path)
#     return extension


def get_last_comics():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    num = response.json()['num']
    return num


def save_img_to_pc(img_url):
    # def save_img_to_pc(img_url, image_title):
    img = urlparse(unquote(img_url)).path.rstrip("/").split("/")[-1]
    response = requests.get(img_url)
    response.raise_for_status()
    # extension = get_extension(url)
    # with open(f'./{image_title}{extension}', 'wb') as file:
    with open(f'./{img}', 'wb') as file:
        file.write(response.content)
        return file.name


def get_comics_from_xkcd():
    """Get comics from https://xkcd.com/"""
    url = f"https://xkcd.com/{random.randrange(1, get_last_comics() + 1)}/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    post = response.json()
    img_url = post['img']
    comics_message = post['alt']
    if img_url:
        img = save_img_to_pc(img_url)
        return img, comics_message


def get_vk_upload_server_url(vk_token, api_version):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {'access_token': vk_token,
              'v': api_version
              }
    response = requests.get(url, params)
    response.raise_for_status()
    upload_url = response.json()["response"]["upload_url"]
    return upload_url


def del_img_from_pc(img):
    if not os.path.isfile(img):
        return
    os.remove(img)


def upload_img_to_vk_album(upload_url, img):
    with open(img, 'rb') as file:
        files = {"photo": file}
        response = requests.post(upload_url, files=files)
    uploaded_photo = response.json()
    server = uploaded_photo['server']
    photo = uploaded_photo['photo']
    photo_hash = uploaded_photo['hash']
    return server, photo, photo_hash


def save_img_to_vk_album(server, photo, img_hash,
                         vk_token, api_version):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {'server': server,
              'photo': photo,
              'hash': img_hash,
              'access_token': vk_token,
              'v': api_version
              }
    response = requests.post(url, params=params)
    response.raise_for_status()
    uploaded_photo = response.json()["response"][0]
    return uploaded_photo['owner_id'], uploaded_photo['id']


def post_img_to_vk_group_wall(group_id, owner_id, media_id,
                              api_version, comics_message,
                              vk_token):
    url = 'https://api.vk.com/method/wall.post'
    params = {
        "access_token": vk_token,
        "v": api_version,
        "attachments": f"photo{owner_id}_{media_id}",
        "owner_id": group_id,
        "from_group": 1,
        "message": comics_message
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    # print(response.text)
    # return response.text


def main():
    api_version = 5.131
    try:
        load_dotenv()
        vk_token = os.environ['VK_API_TOKEN']
        group_id = -int(os.environ['VK_GROUP_ID'])
        img, comics_message = get_comics_from_xkcd()
        upload_url = get_vk_upload_server_url(vk_token, api_version)
        server, photo, img_hash = upload_img_to_vk_album(upload_url, img)
        owner_id, media_id = save_img_to_vk_album(server, photo, img_hash,
                                                  vk_token, api_version)
        post_img_to_vk_group_wall(group_id, owner_id, media_id,
                                  api_version, comics_message,
                                  vk_token)
    except Exception as e:
        print(e)
    finally:
        del_img_from_pc(img)


if __name__ == '__main__':
    main()
