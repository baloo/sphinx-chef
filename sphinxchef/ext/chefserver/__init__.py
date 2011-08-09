# -*- coding: utf-8 -*-
"""
    sphinxchef.ext.chefserver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Allow chef server documentation directly inserted into documentation

    :copyright: Copyright 2011 by Arthur Gautier
    :copyright: Copyright 2011 by Zenexity
    :license: BSD, see LICENSE for details.
"""
# Usual python imports
import posixpath
import os
from os import path
import io

# ReST generator
from docutils import nodes
from docutils.parsers.rst import directives

# Sphinx things
from sphinx.errors import SphinxError
from sphinx.util.osutil import ensuredir, ENOENT, EPIPE
from sphinx.util.compat import Directive
from sphinx.util import copy_static_entry

# Mustache template engine
import pystache
from sphinxchef.ext.chefserver.loader import Loader

# INI config parser
import ConfigParser

# Chef imports
import chef

class ChefserverError(SphinxError):
  category = 'Zenserver error'

class chefserver(nodes.General, nodes.Element):
  """
  This class stores element object of documentation
  """
  config = {}
  def __repr__(self):
    output = []
    for item in self.config.items():
      output.append("%s=\"%s\"" % item)
    return "<%s %s>" % (self.__class__.__name__, " ".join(output))

  def __str__(self):
    """
    String representation of node
    """
    output = []
    for item in self.config.items():
      output.append("%s=\"%s\"" % item)
    return "<%s %s/>" % (self.__class__.__name__, " ".join(output))

  def content(self, builder):
    """
    Gets content against chef server and return dict-like object
    """
    with chef.ChefAPI(builder.config.chefserver_chef,
                      builder.config.chefserver_chef_key,
                      builder.config.chefserver_chef_login):
      n = chef.Node(self.config['fqdn'])
      return n

    return {}

class Chefserver(Directive):
  """
  Directive to insert chef server markup.
  """
  required_arguments = 0
  optional_arguments = 0
  final_argument_whitespace = False
  option_spec = {}
  has_content = True

  needed_content = ['fqdn']

  def get_config(self):
    """
    Gets content of the chefserver directive
    """

    # Get content into an IO fd
    content = io.StringIO()
    content.write(u"[server]\n")
    for str in self.content:
      content.write("%s\n" % str)
    content.seek(0) # Get back to the start

    # Read the content in as INI style
    config = ConfigParser.RawConfigParser()
    config.readfp(content)
    content.close() # We can close buffer
    del content

    # Now read content
    for item in self.needed_content:
      if config.has_option('server', item) == False:
        pass #TODO: this MUST raised exceptions

    # Gets content in a dict
    dict_config = {}
    for item in config.items('server'):
      name, content = item
      dict_config[name] = content

    return dict_config

  def run(self):
    """
    Sphinx calls uses this function as entry point
    """
    node = chefserver()
    node.config = self.get_config()
    return [node]

def html_visit_chefserver(self, node):
  """
  This function generates html content from:
    - Mustache template file
    - Chef infos
  """
  # Gets sources
  filename = node.config.get('filename', self.builder.config.chefserver_default_template)
  markup = Loader().load_template(filename+'.html', self.builder.config.chefserver_templates)
  content = node.content(self.builder)

  # Generate html content
  html = pystache.Template(markup, content).render()
  self.body.append(html)

  # Copy css file
  for file in self.builder.config.chefserver_css_files:
    copy_static_entry(path.join(self.builder.config.chefserver_css_path, file),
      path.join(self.builder.outdir, '_static'),
      self.builder)
    self.builder.css_files.append(path.join('_static', file))

  raise nodes.SkipNode


def setup(app):
  """
  Chefserver plugin entry point
  """
  app.add_node(chefserver,
               html=(html_visit_chefserver, None))
  app.add_directive('chefserver', Chefserver)

  # Templates related configs
  app.add_config_value('chefserver_templates', path.join(path.dirname(__file__), 'templates'), 'html')
  app.add_config_value('chefserver_default_template', 'server', 'html')
  app.add_config_value('chefserver_css_files', ['chefserver.css'], 'html')
  app.add_config_value('chefserver_css_path', path.join(path.dirname(__file__), 'stylesheets'), 'html')

  # Chef related configs
  app.add_config_value('chefserver_chef', '', 'html')
  app.add_config_value('chefserver_chef_key', '', 'html')
  app.add_config_value('chefserver_chef_login', '', 'html')


# EOF
