require 'selenium-webdriver'
require 'active_record'
require 'pry'

class Input < ActiveRecord::Base
  self.table_name = 'inputs'
end

def db_setup
  ActiveRecord::Base.establish_connection(
    adapter: 'mysql2',
    host: 'localhost',
    username: 'root', password: '',
    database: 'register_form',
  ) end

def save(node, label, new_definition=false)
  existing_labels = labels()
  unless (new_definition || existing_labels.include?(label))
    puts "#{label} is newly defined? is it ok?"
    puts "set new_definition flag as save(driver, node, label, true)"
    return
  end

  url = $driver.current_url
  html = node.attribute('outerHTML')
  parent_html = node.find_element(:xpath, "..").attribute('outerHTML')
  Input.create(
    url: url,
    html: html,
    parent_html: parent_html,
    label: label
  )
end

def labels()
  Input.select('label').group('label').map(&:label)
end

def urls()
  Input.select('url').group('url').map(&:url)
end

def visited?(current_url)
  urls.map{ |a| a.split('?')[0] }.include?(current_url.split('?')[0])
end

def find_input_tags
  $driver.find_elements(:xpath, '//input[not(@type="hidden")]')
end

def find_radio_box
  $driver.find_elements(:xpath, '//input[@type="radio"]')
end

def find_select_box
  $driver.find_elements(:xpath, '//select[not(@type="hidden")]')
end

def find_check_box
  $driver.find_elements(:xpath, '//input[@type="checkbox"]')
end

def fill_input_tags(input_tags)
  input_tags.each_with_index do |e, i|
    next unless e.displayed?
    begin
      e.send_keys i.to_s
    rescue => e
      puts e
    end
  end
end

def click_by_js(driver, element)
  $driver.execute_script("return arguments[0].click()", element)
end

def load_highliter()
  script = 'var script = document.createElement("script"); script.type = "text/javascript"; script.src = "https://toshiya.github.io/semantic_selector/static/highlighter.min.js"; document.head.appendChild(script);'
  $driver.execute_script(script)

  sleep(2)

  script = 'window.myHighliter = new window.Highlighter({"color":"red"});'
  $driver.execute_script(script)
end

# TODO: support radio. same name may be used for multiple input tags
def highlight_by_name(name)
  script = "var element = document.getElementsByName(\"#{name}\")[0]; window.myHighliter.point(element);window.myHighliter.underline();"
  $driver.execute_script(script)
end

def erase_by_name(name)
  script = "var element = document.getElementsByName(\"#{name}\")[0]; window.myHighliter.point(element);window.myHighliter.erase();"
  $driver.execute_script(script)
end

db_setup()
$driver = Selenium::WebDriver.for :chrome

binding.pry
$driver.quit
