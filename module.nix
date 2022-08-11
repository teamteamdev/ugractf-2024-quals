{
  services.nginx = {
    commonHttpConfig = ''
      # For ihaitpwbakol
      large_client_header_buffers 4 32k;
    '';

    virtualHosts."ugrac1f.ru" = {
      forceSSL = true;
      enableACME = true;
      locations."/" = {
        root = "/var/lib/q2023_tasks/seeker/html";
      };
    };
  };
}
