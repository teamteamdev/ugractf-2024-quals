using Microsoft.EntityFrameworkCore;
 
namespace pastapp.Models
{
    public class ApplicationContext : DbContext
    {
        public DbSet<User> Users { get; set; } = null!;
        public DbSet<Localization> Localizations { get; set; } = null!;

        public ApplicationContext(DbContextOptions<ApplicationContext> options)
            : base(options){}
    }
}