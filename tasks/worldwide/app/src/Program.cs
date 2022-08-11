using Microsoft.AspNetCore.Routing.Constraints;
using Microsoft.EntityFrameworkCore;
using pastapp.Models;
using Microsoft.IdentityModel.Tokens;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using System.Text;
using Microsoft.AspNetCore.Rewrite;

const string UnixSocketPath = "/sockets/pasta.sock";

if (File.Exists(UnixSocketPath))
{
    File.Delete(UnixSocketPath);
}

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenUnixSocket(UnixSocketPath);
});

var jwtIssuer = builder.Configuration.GetSection("Jwt:Issuer").Get<string>();
var jwtKey = builder.Configuration.GetSection("Jwt:Key").Get<string>();
builder.Services.Configure<RouteOptions>(options =>
{
    options.AppendTrailingSlash = true;
});
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Events = new JwtBearerEvents
        {
            OnMessageReceived = context => {
                context.Token = context.Request.Cookies["session"];
                return Task.CompletedTask;
            }
        };
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwtIssuer,
            ValidateAudience = false,
            ValidateLifetime = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ValidateIssuerSigningKey = true,
         };
});
builder.Services.AddAuthorization();

string connection = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<ApplicationContext>(options => options.UseNpgsql(connection));

builder.Services.AddControllersWithViews();

var app = builder.Build();
app.UseStaticFiles();
app.UseRewriter(new RewriteOptions().AddRedirect("(.*[^/])$", "$1/"));
app.UseStatusCodePages();
app.UseRouting();

app.UseAuthentication();
app.UseAuthorization();


app.MapControllerRoute(
    name: "default",
    pattern: "/{token}/",
    defaults: new {controller = "Home", action = "Index"},
    constraints: new {token = new RegexRouteConstraint(@"[0-9a-f]{16}")}
);
app.MapControllerRoute(
    name: "lang",
    pattern: "/{token}/localization/",
    defaults: new {controller = "Localization", action = "GetPageByLanguage"},
    constraints: new {token = new RegexRouteConstraint(@"[0-9a-f]{16}")}
);
app.MapControllerRoute(
    name: "login",
    pattern: "/{token}/login/",
    defaults: new {controller = "Login", action = "Index"},
    constraints: new {token = new RegexRouteConstraint(@"[0-9a-f]{16}")}
);
app.MapControllerRoute(
    name: "account",
    pattern: "/{token}/account/",
    defaults: new {controller = "Account", action = "Index"},
    constraints: new {token = new RegexRouteConstraint(@"[0-9a-f]{16}")}
);
app.Run();