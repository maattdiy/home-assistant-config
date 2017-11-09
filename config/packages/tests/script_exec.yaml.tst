## Script Exec HASS Module
    
##################################################
## Scripts
##################################################

script:
  exec:
    sequence:
      - service: python_script.script_exec
        data_template:
          name: "{{ name }}"
          msg: "{{ msg }}"
          inner_data: "{{ data }}"
