from .exceptions import NoSuchProviderError
from .configs import configs
import logging
import os


class Provider(object):
    params = None

    def __init__(self, config):
        self.config = configs[config]

    def get_content(self, file):
        ...

    def get_path(self, path):
        ...

    def save(self, file, content):
        ...

    def delete(self, path):
        ...

    def build(self):
        return False

    def delete_hooks(self):
        return False

    def create_hook(self, config):
        return False

    def get_tree(self, path, depth):  # run if depth >=1
        if not depth:
            return []
        path = path.replace("\\", "/")
        tree = self.get_path(path)["data"]
        for i in range(len(tree)):
            if tree[i]["type"] == "dir":
                child = self.get_tree(tree[i]["path"], depth - 1)
                tree += child
        return tree

    def get_posts(self):
        _posts = list()
        _drafts = list()
        names = list()
        try:
            for path_index in range(len(self.config["drafts"]["path"])):
                drafts = self.get_tree(
                    self.config["drafts"]["path"][path_index], self.config["drafts"]["depth"][path_index])
                for i in range(len(drafts)):
                    flag = False
                    for j in self.config["drafts"]["type"]:
                        if drafts[i]["path"].endswith(j):
                            flag = j
                            break
                    if drafts[i]["type"] == "file" and flag:
                        name = drafts[i]["path"].split(
                            self.config["drafts"]["path"][path_index] if self.config["drafts"]["path"][path_index][-1] == "/" else
                            self.config["drafts"]["path"][path_index] + "/")[1]
                        name = name[:-len(flag) - (1 if name[-1] == "/" else 0)]
                        _drafts.append({"name": name,
                                        "fullname": drafts[i]["path"].split(
                                            self.config["drafts"]["path"][path_index] if self.config["drafts"]["path"][path_index][
                                                                                             -1] == "/" else self.config["drafts"]["path"][
                                                                                                                 path_index] + "/")[1],
                                        "path": drafts[i]["path"],
                                        "size": drafts[i]["size"],
                                        "status": False})

                        names.append(drafts[i]["path"].split(
                            self.config["drafts"]["path"][path_index])[1])
        except Exception as e:
            logging.error("读取草稿错误: {}，跳过".format(repr(e)))
        try:
            for path_index in range(len(self.config["posts"]["path"])):
                posts = self.get_tree(
                    self.config["posts"]["path"][path_index], self.config["posts"]["depth"][path_index])
                for i in range(len(posts)):
                    flag = False
                    for j in self.config["posts"]["type"]:
                        if posts[i]["path"].endswith(j):
                            flag = j
                            break
                    if posts[i]["type"] == "file" and flag:
                        name = posts[i]["path"].split(
                            self.config["posts"]["path"][path_index] if self.config["posts"]["path"][path_index][-1] == "/" else
                            self.config["posts"]["path"][path_index] + "/")[1]
                        name = name[:-len(flag) - (1 if name[-1] == "/" else 0)]
                        _posts.append({"name": name,
                                       "fullname": posts[i]["path"].split(
                                           self.config["posts"]["path"][path_index] if self.config["posts"]["path"][path_index][
                                                                                           -1] == "/" else self.config["posts"]["path"][
                                                                                                               path_index] + "/")[1],
                                       "path": posts[i]["path"],
                                       "size": posts[i]["size"],
                                       "status": True})
                        names.append(posts[i]["path"].split(
                            self.config["posts"]["path"][path_index])[1])
        except Exception as e:
            logging.error("读取已发布错误: {}，跳过".format(repr(e)))
        posts = _posts + _drafts
        logging.info("读取文章列表成功")
        return posts

    def get_pages(self):
        results = list()
        for path_index in range(len(self.config["pages"]["path"])):
            try:
                posts = self.get_tree(
                    self.config["pages"]["path"][path_index], self.config["pages"]["depth"][path_index])
                for post in posts:
                    flag = False
                    for i in self.config["pages"]["type"]:
                        if post["path"].endswith(i):
                            flag = i
                            break
                    if post["type"] == "file" and flag:
                        results.append({"name": post["path"][len(self.config["pages"]["path"][path_index]) + (
                            0 if self.config["pages"]["path"][path_index].endswith("/") else 1):-len(flag) - 1],
                                        "path": post["path"],
                                        "size": post["size"]})
            except Exception as e:
                logging.error("读取页面 {} 错误: {}，跳过".format(self.config["pages"]["path"][path_index], repr(e)))
        logging.info("读取页面列表成功")
        return results

    def get_configs(self):
        results = list()
        for path_index in range(len(self.config["configs"]["path"])):
            try:
                posts = self.get_tree(
                    self.config["configs"]["path"][path_index], self.config["configs"]["depth"][path_index])
                for post in posts:
                    flag = False
                    for i in self.config["configs"]["type"]:
                        if post["path"].endswith(i):
                            flag = True
                            break
                    if post["type"] == "file" and flag:
                        results.append({"name": post["path"][len(self.config["configs"]["path"][path_index]) + (
                            0 if self.config["configs"]["path"][path_index].endswith("/") else 1):],
                                        "path": post["path"],
                                        "size": post["size"]})
            except Exception as e:
                logging.error("读取页面 {} 错误: {}，跳过".format(self.config["configs"]["path"][path_index], repr(e)))
        logging.info("读取博客配置列表成功")
        return results

    def get_scaffold(self, scaffold_type):
        return self.get_content(self.config[scaffold_type]["scaffold"])

    def save_post(self, name, content, path=None, status=False):
        # status: True -> posts, False -> drafts
        # path 若无则保存至默认路径
        draft_file = self.config["drafts"]["save_path"].replace("${filename}", name)
        save_file = self.config["posts"]["save_path"].replace("${filename}", name)
        if path and (path not in [draft_file, save_file]):
            return [self.save(path, content, f"Save Post {name} by Qexo"), path]
        if status:
            try:
                self.delete(draft_file, f"Delete Post Draft {draft_file} by Qexo")
            except:
                logging.info(f"删除草稿{draft_file}失败, 可能无需删除草稿")
            return [self.save(save_file, content, f"Publish Post {save_file} by Qexo"), save_file]
        else:
            return [self.save(self.config["drafts"]["save_path"].replace("${filename}", name), content,
                              f"Save Post Draft {draft_file} by Qexo"), draft_file]

    def save_page(self, name, content):
        path = self.config["pages"]["save_path"].replace("${filename}", name)
        return [self.save(path, content, f"Update Page {name}"), path]


from .providers import _all_providers


def all_providers():
    return list(_all_providers.keys())


def get_params(provider_name):
    if provider_name not in _all_providers:
        raise NoSuchProviderError(provider_name)
    return _all_providers[provider_name].params


def get_provider(provider_name: str, **kwargs):
    if provider_name not in _all_providers:
        raise NoSuchProviderError(provider_name)
    return _all_providers[provider_name](**kwargs)
